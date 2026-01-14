# Trash Bin

> Do not worry about accidentally deleting any data sources or templates again!

---

## Use the `delete` parm to delete items

The following set of commands support the `delete` parameter to delete items

- Chat history
```bash
llf chat history delete SESSION_ID
```
Note:  The deleted items are moved to `trash/chat_history`

- Data Stores (RAG Vector Store)
```bash
llf datastore delete DATA_STORE_NAME
```
Note:  The deleted items are moved to `trash/datastores`

- Long Term Memory modules
```bash
llf memory delete MEMORY_NAME
```

Note:  The deleted items are moved to `trash/memories`

- Prompt Templates
```bash
llf prompt delete TEMPLATE_NAME
```

Note:  The deleted items are moved to `trash/templates`

---

## There is one `delete` that is permanent

The following `delete` command can not be undone

When a user deletes an LLM model, it is perminanetly deleted and will need to be re-downloaded.  This was excluded from the `trash` undelete option due to their size and the fact that they can be easily re-downloaded.

Here is an example of the command:
```bash
llf model delete Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

---

## Managing the trash

Here you will see how to view the trash content, how to perform restores, and how to empty the trash

The help information
```bash
llf trash -h
```

**Example Output:**
```
usage: llf trash [-h] [--type {memory,datastore,chat_history,template}] [--older-than DAYS] [--all] [--force] [--dry-run]

Manage deleted items with 30-day recovery. View, restore, or permanently delete items from trash.

...

actions:
  list                             List all items in trash
  list --type memory               List only memory items in trash
  list --older-than 30             List items older than 30 days
...
```

How to view the trash content
```bash
llf trash list
```

**Example Output:**
```
Trash ID          ┃ Type         ┃ Name                     ┃ Age (days)
20260114_230707   │ chat_history │ 20260114_170648_296734   │          0
```

How to view detailed information about a deleted item
```bash
llf trash info 20260114_230707
```

How to restore an item
```bash
llf trash restore 20260114_230707
```

How to delete all the items older then 5 days from the trash
```bash
llf trash empty --older-than 5
```
