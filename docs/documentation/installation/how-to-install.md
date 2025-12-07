# How to install

## Prerequisites
 
  - Install [pydantic](https://pypi.org/project/pydantic) — ✅ required, 
  - Install [openai](https://pypi.org/project/openai) to use OpenAI models — 🔸 optional.
  - Install [boto3](https://pypi.org/project/boto3/) to use AWS Bedrock models — 🔸 optional.
  - Install [numpy](https://pypi.org/project/numpy/) to use Embedding, `FAISSVectorStore` — 🔸 optional.
  - Install [faiss-cpu](https://pypi.org/project/faiss-cpu/) to use `FAISSVectorStore` — 🔸 optional.
  - Install [typing_extensions](https://pypi.org/project/typing-extensions/) to use state in `FlowEngine` — 🔸 optional.
  - Install [redis](https://pypi.org/project/redis/) to use `RedisCheckpointer` — 🔸 optional.
  - Install [SQLAlchemy](https://pypi.org/project/SQLAlchemy/) to use `SQLCheckpointer` — 🔸 optional. `SQLCheckpointer` supports both sync and async drivers for multiple databases:
      - PostgreSQL (async: [asyncpg](https://pypi.org/project/asyncpg/), sync: [psycopg2](https://pypi.org/project/psycopg2/)) — 🔸 optional.
      - MySQL (async: [aiomysql](https://pypi.org/project/aiomysql/), sync: [pymysql](https://pypi.org/project/PyMySQL/)) — 🔸 optional.
      - SQLite (async: [aiosqlite](https://pypi.org/project/aiosqlite/), sync: built-in) — 🔸 optional.

### Using pip
```shell
pip install llmfy
```
### Using requirements.txt
#### Add into requirements.txt
```shell
llmfy
```
#### Then install
```shell
pip install -r requirements.txt
```
