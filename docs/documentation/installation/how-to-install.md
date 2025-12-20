# How to install

## Prerequisites
 
| Package | Required/Optional | Purpose |
|---------|-------------------|---------|
| [pydantic](https://pypi.org/project/pydantic) | ✅ Required | Core dependency |
| [openai](https://pypi.org/project/openai) | 🔸 Optional | Use OpenAI models |
| [boto3](https://pypi.org/project/boto3/) | 🔸 Optional | Use AWS Bedrock models |
| [numpy](https://pypi.org/project/numpy/) | 🔸 Optional | Use Embedding, `FAISSVectorStore` |
| [faiss-cpu](https://pypi.org/project/faiss-cpu/) | 🔸 Optional | Use `FAISSVectorStore` |
| [typing_extensions](https://pypi.org/project/typing-extensions/) | 🔸 Optional | Use state in `FlowEngine` |
| [redis](https://pypi.org/project/redis/) | 🔸 Optional | Use `RedisCheckpointer` |
| [SQLAlchemy](https://pypi.org/project/SQLAlchemy/) | 🔸 Optional | Use `SQLCheckpointer` (supports sync and async drivers) |

- SQLCheckpointer

    | Package | Required/Optional | Purpose |
    |---------|-------------------|---------|
    | [asyncpg](https://pypi.org/project/asyncpg/) | 🔸 Optional | PostgreSQL async driver for `SQLCheckpointer` |
    | [psycopg2](https://pypi.org/project/psycopg2/) | 🔸 Optional | PostgreSQL sync driver for `SQLCheckpointer` |
    | [aiomysql](https://pypi.org/project/aiomysql/) | 🔸 Optional | MySQL async driver for `SQLCheckpointer` |
    | [pymysql](https://pypi.org/project/PyMySQL/) | 🔸 Optional | MySQL sync driver for `SQLCheckpointer` |
    | [aiosqlite](https://pypi.org/project/aiosqlite/) | 🔸 Optional | SQLite async driver for `SQLCheckpointer` |

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
