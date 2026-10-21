import asyncio
from app.core.database import Base, engine
import app.models  # 触发所有模型注册

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("表已创建/确认")
    await engine.dispose()

asyncio.run(main())
