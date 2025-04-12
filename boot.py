import os
import logging
from flask import Flask
from flask_restful import Resource, Api

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    api = Api(app)

    class HealthCheck(Resource):
        def get(self):
            logger.info("ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋ ᴇɴᴅᴘᴏɪɴᴛ ᴡᴀꜱ ʀᴇᴀᴄʜᴇᴅ")
            return {
                "status": "ᴏᴘᴇʀᴀᴛɪᴏɴᴀʟ",
                "service": "ᴠx ᴀɪ ꜱʏꜱᴛᴇᴍ",
                "message": "ꜱʏꜱᴛᴇᴍ ɪꜱ ʀᴇᴀᴅʏ"
            }

    api.add_resource(HealthCheck, '/')

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"ꜱᴛᴀʀᴛɪɴɢ ᴠx ᴀɪ ꜱᴇʀᴠᴇʀ ᴏɴ ᴘᴏʀᴛ {port}")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("DEBUG", "false").lower() == "true"
    )
