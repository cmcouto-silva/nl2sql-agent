# Building a SQL Agent with n8n

For this tutorial, we'll use [n8n](https://n8n.io/): a flexible low-code AI workflow automation.  
n8n provides over 5k workflow templates with prebuilt automation. Here, we'll use the [Chat with PostgreSQL Database](https://n8n.io/workflows/2859-chat-with-postgresql-database/).

## Install & run n8n:

```bash
docker run -d --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

Then, access http://localhost:5678 and setup your admin user.

## Set credentials

We'll need to set up the credentials for OpenAI Postgres database connection.  

Locate "Create Workflow" at the top right of the page, click at the arrow and select "Create Credential". Search for and select OpenAi and Postgres.

If you're hosting a local database setup using docker, use: `host.docker.internal` instead of `localhost`.

> While we're using OpenAI and Postgres in this tutorial, be aware that you can choose other LLM providers and database engines.

## Import template

Create a new workflow. Locate the three dots at the top right panel, click on "Import from file", and then select the file `chat_with_postgresql_database.json` on the folder `artifacts`.

## Play with the agent

1. Modify the OpenAI model to gpt-4.1-mini
2. Run separately the "Get DB Schema and Tables List" tool at least once for testing/updating Postgres connection.
3. Chat with your agent :)
