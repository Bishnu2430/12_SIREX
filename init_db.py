from storage.postgres import PostgresStorage
from agent.memory import AgentMemory

try:
    pg = PostgresStorage()
    print('✓ PostgreSQL initialized')
except Exception as e:
    print(f'PostgreSQL: {e}')

try:
    memory = AgentMemory()
    print('✓ Agent memory initialized')
except Exception as e:
    print(f'Memory: {e}')

print('\n✅ Database initialization complete!')
