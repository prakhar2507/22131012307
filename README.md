### ✅ `README.md`

```markdown
# FastAPI URL Shortener with Logging Middleware

This is a minimal and efficient URL shortening microservice built with **FastAPI**. It features:
- URL shortening with optional custom shortcodes.
- Expiry management.
- Redirection support.
- Click analytics (IP, referrer, timestamp).
- Centralized structured logging via a custom middleware.

---

## 📦 Project Structure

```

project-root/
├── main.py
├── logging\_middleware/
│   ├── **init**.py
│   ├── logger.py
│   └── middleware.py

````

---

## 🚀 Running the Project

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
````

2. **Start the FastAPI server**

   ```bash
   python main.py
   ```

---

## 📌 Approach

* All URLs and metadata are stored in an in-memory dictionary `storage` using the shortcode as the key.
* Each URL entry tracks:

  * Original URL
  * Creation time
  * Expiry time
  * Number of clicks
  * Click metadata (IP, referrer, timestamp)
* A reusable `log()` function sends logs to a central logging endpoint.
* `LoggingMiddleware` logs each HTTP request and response.

---

## 📘 API Endpoints

### 🔹 POST `/shorturls`

Creates a shortened URL.

#### ✅ Request Body

```json
{
  "url": "https://example.com",
  "validity": 30,
  "shortcode": "custom123"   // Optional
}
```

* `url`: required, a valid URL.
* `validity`: optional, duration in minutes (default: 30).
* `shortcode`: optional, alphanumeric custom shortcode (max 10 chars).

#### ✅ Response

```json
{
  "shortLink": "http://localhost:8000/custom123",
  "expiry": "2025-06-27T10:22:31.567766Z"
}
```

---

### 🔹 GET `/{shortcode}`

Redirects to the original URL using the provided shortcode.

#### ✅ Example

```
GET http://localhost:8000/test124
```

* If the shortcode is valid and not expired, redirects (302) to the original URL.
* Otherwise, returns a 404 or 410 error.

---

### 🔹 GET `/shorturls/{shortcode}`

Returns statistics about a shortened URL.

#### ✅ Example

```
GET http://localhost:8000/shorturls/test124
```

#### ✅ Response

```json
{
  "original_url": "https://example.com",
  "created_at": "2025-06-27T10:12:31.567766Z",
  "expiry": "2025-06-27T10:42:31.567766Z",
  "clicks": 3,
  "click_details": [
    {
      "timestamp": "2025-06-27T10:15:00.123Z",
      "referrer": "https://google.com",
      "ip": "192.168.0.1"
    }
  ]
}
```

---

## 🛠️ Logging Middleware

Each request is logged using the following structure:

```json
{
  "stack": "backend",
  "level": "info",
  "package": "middleware",
  "message": "Incoming request: GET /test123"
}
```

Centralized logs are sent to:

```
http://20.244.56.144/evaluation-service/logs
```
