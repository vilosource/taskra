# Jira Cloud REST API Reference: Projects, Issues, and Worklogs

This guide covers common Jira Cloud REST API v3 endpoints for **projects**, **issues**, and **worklogs**. All endpoints are under the base URL:

```
https://your-domain.atlassian.net/rest/api/3/
```

Authentication is required for all endpoints, typically via Basic Auth (email + API token) or OAuth2. All requests and responses use JSON. Set headers:

```
Content-Type: application/json
Accept: application/json
```

---

## Projects

### List Projects
- **Endpoint:** `GET /project/search`
- **Description:** Retrieves a paginated list of projects visible to the user.
- **Query Parameters:**
  - `startAt` (int): Index of the first project.
  - `maxResults` (int): Max number of projects (max: 50).
  - `orderBy` (string): Field to sort by (`name`, `key`, etc.).
  - `id`, `keys` (array): Filter by project ID/key.
  - `query` (string): Search by name/key.
  - `typeKey` (string): Project type (`software`, `business`, etc.).
  - `categoryId` (int): Filter by category ID.
  - `action` (string): Permission filter (`view`, `browse`, `edit`).
  - `expand` (string): Additional fields like `description`, `lead`, etc.

#### Example Request
```http
GET /rest/api/3/project/search?maxResults=2&orderBy=name
```

#### Example Response
```json
{
  "startAt": 0,
  "maxResults": 2,
  "total": 7,
  "isLast": false,
  "values": [
    {
      "id": "10000",
      "key": "EX",
      "name": "Example",
      "projectTypeKey": "software",
      "avatarUrls": { ... },
      "projectCategory": { ... },
      "insight": { "totalIssueCount": 100 }
    }
  ]
}
```

---

### Get Project
- **Endpoint:** `GET /project/{projectIdOrKey}`
- **Description:** Returns detailed information for a single project.
- **Path Parameters:**
  - `projectIdOrKey` (string): Project ID or key.
- **Query Parameters:**
  - `expand` (string): Additional fields.

#### Example Request
```http
GET /rest/api/3/project/EX?expand=description,lead
```

#### Example Response
```json
{
  "id": "10000",
  "key": "EX",
  "name": "Example",
  "description": "This is an example project.",
  "lead": {
    "accountId": "5b10a2844c20165700ede21g",
    "displayName": "Alice Doe"
  }
}
```

---

## Issues

### Create Issue
- **Endpoint:** `POST /issue`
- **Description:** Creates a new issue or sub-task.
- **Body Parameters:**
```json
{
  "fields": {
    "project": { "key": "EX" },
    "issuetype": { "id": "10001" },
    "summary": "Issue summary",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "Issue description." }] }
      ]
    }
  }
}
```

#### Example Response
```json
{
  "id": "10000",
  "key": "EX-1",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000"
}
```

---

### Get Issue
- **Endpoint:** `GET /issue/{issueIdOrKey}`
- **Description:** Returns detailed information for a specific issue.
- **Path Parameters:**
  - `issueIdOrKey` (string): ID or key.
- **Query Parameters:**
  - `fields`, `expand`, `updateHistory`, etc.

#### Example Request
```http
GET /rest/api/3/issue/EX-1?fields=summary,status,assignee
```

#### Example Response
```json
{
  "id": "10001",
  "key": "EX-1",
  "fields": {
    "summary": "Issue summary",
    "status": { "name": "Done" },
    "assignee": { "accountId": "...", "displayName": "Alice" }
  }
}
```

---

## Worklogs

### Add Worklog
- **Endpoint:** `POST /issue/{issueIdOrKey}/worklog`
- **Description:** Adds a worklog entry (time spent).
- **Body Parameters:**
```json
{
  "timeSpentSeconds": 7200,
  "started": "2025-03-27T14:00:00.000+0300",
  "comment": "Worked on feature."
}
```

#### Example Response
```json
{
  "id": "10001",
  "timeSpent": "2h",
  "author": { "displayName": "Alice" },
  "comment": "Worked on feature."
}
```

---

### List Worklogs
- **Endpoint:** `GET /issue/{issueIdOrKey}/worklog`
- **Description:** Returns all worklogs for an issue.
- **Query Parameters:**
  - `startAt`, `maxResults`, `startedAfter`, `expand`

#### Example Request
```http
GET /rest/api/3/issue/EX-1/worklog?maxResults=50
```

#### Example Response
```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 2,
  "worklogs": [
    {
      "id": "10001",
      "author": { "displayName": "Alice" },
      "timeSpent": "2h",
      "comment": "Worked on feature."
    }
  ]
}
```

---

> **Note:** Use proper permissions and rate-limiting strategies. Always check the [Atlassian Developer API docs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/) for the most up-to-date references.

