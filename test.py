import os
from dotenv import load_dotenv
load_dotenv()

print("SERVER:", os.getenv("SERVER"))
print("DATABASE:", os.getenv("DATABASE"))
print("DRIVER:", os.getenv("DRIVER"))
