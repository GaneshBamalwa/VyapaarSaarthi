import asyncio
from app.agents.collections.message_generator import generate_reminder_message

async def run():
    res = await generate_reminder_message('Suresh Enterprises', 1, 1500, 15, 2, 'Vyapaar Saarthi')
    print('MSG:')
    print(res.encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(run())
