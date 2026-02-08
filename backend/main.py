from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import shutil
from typing import Optional, Dict, Any

from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise.crypto import WeChatCrypto

from core.config_manager import ConfigManager
from core.file_scanner import FileScanner
from core.wecom_client import WeComClient
from core.scheduler_service import SchedulerService

# Setup Logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="企业微信文件自动发送系统",
    version="1.0.0",
    description="自动监控指定文件夹，并将最新文件通过企业微信发送给指定用户。"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_manager = ConfigManager()
scheduler = SchedulerService()

# --- Task Logic ---
def execute_task():
    logging.info("任务开始执行")
    config = config_manager.load_config()
    
    monitor_folder = config.get("monitor_folder")
    if not monitor_folder:
        logging.error("未配置监控文件夹")
        return

    # 1. Scan
    latest_file = FileScanner.get_latest_file(monitor_folder)
    if not latest_file:
        logging.info("未找到可发送的文件")
        return
    
    logging.info(f"找到最新文件: {latest_file}")

    # 2. WeCom Init
    wecom_conf = config.get("wecom", {})
    client = WeComClient(
        corpid=wecom_conf.get("corpid"),
        secret=wecom_conf.get("secret"),
        agentid=wecom_conf.get("agentid")
    )

    # 3. Upload
    media_id = client.upload_media(latest_file)
    if not media_id:
        logging.error("文件上传失败")
        return
    
    # 4. Send
    success = client.send_file_message(
        media_id=media_id,
        touser=wecom_conf.get("touser", "@all"),
        toparty=wecom_conf.get("toparty", "")
    )

    if success:
        logging.info(f"文件发送成功: {os.path.basename(latest_file)}")
    else:
        logging.error("消息发送失败")

# Initialize Scheduler based on config
def init_scheduler():
    config = config_manager.load_config()
    sched_conf = config.get("schedule", {})
    if sched_conf.get("enabled"):
        scheduler.update_job(
            time_str=sched_conf.get("time", "09:00"),
            frequency=sched_conf.get("frequency", "daily"),
            task_func=execute_task
        )
        scheduler.start()
    else:
        scheduler.stop()

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    init_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.stop()

# --- Models ---
class ConfigModel(BaseModel):
    monitor_folder: str
    wecom: Dict[str, Any]
    schedule: Dict[str, Any]

# --- Endpoints ---

@app.get("/api/status")
def get_status():
    return {
        "running": scheduler.is_running(),
        "next_run": str(scheduler.get_next_run()) if scheduler.get_next_run() else None
    }

@app.get("/api/config")
def get_config():
    return config_manager.load_config()

@app.post("/api/config")
def update_config(config: ConfigModel):
    config_manager.save_config(config.dict())
    init_scheduler() # Restart scheduler with new config
    return {"status": "ok", "message": "Config updated"}

@app.post("/api/run")
def run_now():
    # Run in background to not block request? 
    # For simplicity, run sync or maybe async. 
    # Since execute_task does network I/O, better be async or in thread.
    # But for this MVP, let's just call it.
    try:
        execute_task()
        return {"status": "ok", "message": "Task executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    config = config_manager.load_config()
    monitor_folder = config.get("monitor_folder")
    
    if not monitor_folder:
        raise HTTPException(status_code=500, detail="Monitor folder not configured")
        
    if not os.path.exists(monitor_folder):
        os.makedirs(monitor_folder)
        
    file_path = os.path.join(monitor_folder, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"文件上传成功: {file.filename}")
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        logging.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
def get_logs(lines: int = 50):
    if not os.path.exists("app.log"):
        return {"logs": []}
    
    try:
        with open("app.log", "r", encoding='utf-8') as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception:
        return {"logs": []}

import urllib.parse
import hashlib

@app.get("/api/wecom/callback")
def wecom_callback(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    # Log raw received params
    logging.info(f"DEBUG: Raw params - sig={msg_signature}, ts={timestamp}, nonce={nonce}, echo={echostr}")
    
    # Decode echostr (important!)
    echostr_decoded = urllib.parse.unquote(echostr)
    
    config = config_manager.load_config()
    wecom_conf = config.get("wecom", {})
    token = wecom_conf.get("token")
    aes_key = wecom_conf.get("aes_key")
    corpid = wecom_conf.get("corpid")
    
    if not token or not aes_key or not corpid:
         logging.error("回调验证失败: Token, AES Key 或 CorpID 未配置")
         raise HTTPException(status_code=400, detail="Config missing")

    # Manual Signature Check to debug
    try:
        sort_list = [token, timestamp, nonce, echostr_decoded]
        sort_list.sort()
        sha = hashlib.sha1()
        sha.update("".join(sort_list).encode("utf-8"))
        calculated_signature = sha.hexdigest()
        logging.info(f"DEBUG: Calculated sig: {calculated_signature} vs Received: {msg_signature}")
    except Exception as e:
        logging.error(f"DEBUG Error: {e}")

    try:
        # Skip standalone check_signature, go straight to crypto
        logging.info("Initializing WeChatCrypto...")
        if len(aes_key) != 43:
             logging.error(f"CRITICAL: AES Key length is {len(aes_key)}, expected 43!")
        
        crypto = WeChatCrypto(token, aes_key, corpid)
        logging.info("WeChatCrypto initialized.")
        
        logging.info("Decrpyting...")
        # Since signature is already manually checked, we can use decrypt_message directly if check_signature is missing?
        # But for echostr, it is just a string, not XML.
        # Actually, check_signature IS available in WeChatCrypto source usually. 
        # But if it is missing, maybe we should use decrypt_echo? 
        # Let's inspect available methods or try to use _decrypt directly if needed.
        # Wait, echostr is special. 
        
        # In newer wechatpy, maybe check_signature is removed?
        # Let's try to find alternative.
        
        # Workaround: manually decrypt
        try:
             decrypted_echo = crypto.check_signature(
                msg_signature,
                timestamp,
                nonce,
                echostr_decoded
            )
        except AttributeError:
             # Fallback for versions where check_signature might be named differently or missing
             logging.warning("AttributeError: check_signature not found. Trying manual decryption.")
             # The echostr is encrypted using AES.
             # WeChatCrypto.decrypt_message usually expects XML, but here it is a string.
             # We can try crypto._decrypt(echostr_decoded, corpid) if available?
             # Or maybe it is crypto.decrypt_message(echostr_decoded, receive_id=corpid)
             
             # Let's try verify_echo_str if available? No.
             
             # Actually, let's look at how wechatpy implements it.
             # It seems check_signature WAS there.
             pass
             
        # Re-raise if not handled
        decrypted_echo = crypto.check_signature(
            msg_signature,
            timestamp,
            nonce,
            echostr_decoded
        )
        
        # Ensure it's a string
        if isinstance(decrypted_echo, bytes):
            decrypted_echo = decrypted_echo.decode('utf-8')
            
        logging.info(f"回调验证成功! Decrypted Echo: {decrypted_echo}")
        return Response(content=decrypted_echo, media_type="text/plain")
        
    except Exception as e:
         import traceback
         logging.error(f"Fatal Error in callback: {e}")
         logging.error(traceback.format_exc())
         return Response(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
