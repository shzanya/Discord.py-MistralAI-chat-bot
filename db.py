import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

class ShardedDatabase:
    def __init__(self, shard_count=2):
        self.shard_count = shard_count
        self.connections = {}
        
        # Инициализация соединений для каждого шарда
        for shard_id in range(shard_count):
            self.connections[shard_id] = mysql.connector.connect(
                host=os.getenv(f'MYSQL_HOST_{shard_id}', 'localhost'),
                user=os.getenv(f'MYSQL_USER_{shard_id}', 'root'),
                password=os.getenv(f'MYSQL_PASSWORD_{shard_id}', ''),
                database=os.getenv(f'MYSQL_DATABASE_{shard_id}', f'discord_bot_shard_{shard_id}')
            )

    def get_shard_id(self, thread_id: int) -> int:
        """Определяет шард по thread_id"""
        return thread_id % self.shard_count

    def save_message(self, thread_id: int, user_id: int, role: str, content: str):
        """Сохраняет сообщение в соответствующий шард"""
        shard_id = self.get_shard_id(thread_id)
        connection = self.connections[shard_id]
        cursor = connection.cursor()
        
        sql = "INSERT INTO messages (thread_id, user_id, role, content) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (thread_id, user_id, role, content))
        connection.commit()
        cursor.close()

    def get_thread_history(self, thread_id: int, limit: int = 10):
        """Получает историю сообщений из соответствующего шарда"""
        shard_id = self.get_shard_id(thread_id)
        connection = self.connections[shard_id]
        cursor = connection.cursor(dictionary=True)
        
        sql = """SELECT role, content, user_id, created_at 
                 FROM messages 
                 WHERE thread_id = %s 
                 ORDER BY created_at DESC 
                 LIMIT %s"""
        cursor.execute(sql, (thread_id, limit))
        messages = cursor.fetchall()
        cursor.close()
        
        if messages:
            messages.reverse()  # Сначала старые сообщения
        return messages or []

    def init_db(self):
        """Инициализация таблиц для всех шардов"""
        for shard_id in range(self.shard_count):
            connection = self.connections[shard_id]
            cursor = connection.cursor()
            
            # Создание таблицы messages если не существует
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                thread_id BIGINT,
                user_id BIGINT,
                role ENUM('user', 'assistant', 'system'),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Создание индекса если не существует
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_NAME = 'messages' AND INDEX_NAME = 'idx_thread_id'
            """)
            exists = cursor.fetchone()[0]
            if not exists:
                cursor.execute("CREATE INDEX idx_thread_id ON messages(thread_id)")
            
            connection.commit()
            cursor.close()

# Создаем глобальный экземпляр базы данных
db = ShardedDatabase()
