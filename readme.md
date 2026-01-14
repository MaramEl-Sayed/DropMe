# DropMe Backend System

A minimal but functional backend service for the Drop Me recycling flow: **Scan → Recycle → Earn Points**.

Built with **Django + Django REST Framework**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [System Flow](#system-flow)
- [Setup & Installation](#setup--installation)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Business Rules](#business-rules)
- [Assumptions & Trade-offs](#assumptions--trade-offs)
- [Project Structure](#project-structure)

---

## Overview

This backend system supports the core recycling flow where users:
1. **Register** with their name and phone number
2. **Recycle** materials (plastic, cans) at recycling machines
3. **Earn points** based on material type and quantity
4. **Track** their accumulated points

### Key Features

- ✅ User registration with phone number
- ✅ Recycling transaction creation
- ✅ Automatic points calculation and updates
- ✅ Duplicate scan prevention (fraud protection)
- ✅ Input validation & error handling
- ✅ Atomic database transactions (data integrity)
- ✅ Database indexes for performance

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                     │
│              (Mobile App / Web Frontend / Machine)          │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Django REST Framework                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Views      │  │ Serializers  │  │    URLs      │       │
│  │  (API Logic) │  │ (Validation) │  │  (Routing)   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│  ┌───────────────────────▼──────────────────────┐           │
│  │              Business Logic Layer            │           │
│  │  ┌──────────────┐      ┌──────────────┐      │           │
│  │  │   rules.py   │      │ constants.py │      │           │
│  │  │ (Points Calc)│      │ (Config Vals)│      │           │
│  │  └──────────────┘      └──────────────┘      │           │
│  └───────────────────────┬──────────────────────┘           │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      Data Layer (Django ORM)                   │
│  ┌──────────────────┐          ┌─────────────────────┐         │
│  │   User Model     │          │ RecyclingTransaction│         │
│  │  - id (PK)       │◄─────────│  - user (FK)        │         │
│  │  - name          │          │  - material_type    │         │
│  │  - phone         │          │  - quantity         │         │
│  │  - points        │          │  - points_awarded   │         │
│  │  - is_active     │          │  - timestamp        │         │
│  └──────────────────┘          └─────────────────────┘         │
└───────────────────────────┬────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                    SQLite Database (Development)                  │
│                   (Can be switched to PostgreSQL)                 │
└───────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ POST /api/register/
     │ {name, phone}
     ▼
┌─────────────────┐
│ RegisterUserView│
└────┬────────────┘
     │
     │ UserSerializer.validate()
     ▼
┌─────────────────┐
│  User Model     │──┐
│  (Create User)  │  │
└─────────────────┘  │
                     │
                     │ POST /api/recycle/
                     │ {user_id, material_type, quantity}
                     ▼
              ┌──────────────────────┐
              │RecyclingTransaction  │
              │      View            │
              └──────┬───────────────┘
                     │
                     │ RecyclingTransactionSerializer
                     │  1. validate() - Check user, material, quantity
                     │  2. validate() - Check duplicate scan
                     │  3. create() - Atomic transaction:
                     │     - Calculate points (rules.py)
                     │     - Create transaction record
                     │     - Update user.points
                     ▼
              ┌──────────────────────┐
              │  Database (Atomic)   │
              │  - Transaction saved │
              │  - Points updated    │
              └──────────────────────┘
```

---

## System Flow

### User Registration Flow

```
User Request
    │
    ▼
[Validate Input]
    │
    ├─ Phone missing? ──► Error 400
    ├─ Name missing? ──► Error 400
    └─ Valid? ──────────►
                        │
                        ▼
                   [Create User]
                        │
                        ▼
                   [Return User Data]
                   Status: 201 Created
```

### Recycling Transaction Flow

```
Recycling Request
    │
    ▼
[Validate User]
    │
    ├─ User not found? ──► Error 400
    ├─ User inactive? ───► Error 400
    └─ Valid? ───────────►
                          │
                          ▼
                     [Validate Material]
                          │
                          ├─ Invalid? ──► Error 400
                          └─ Valid? ────►
                                        │
                                        ▼
                                   [Validate Quantity]
                                        │
                                        ├─ ≤ 0? ──► Error 400
                                        └─ Valid? ──►
                                                    │
                                                    ▼
                                          [Check Duplicate Scan]
                                                    │
                                                    ├─ Duplicate? ──► Error 400
                                                    └─ Valid? ───────►
                                                                     │
                                                                     ▼
                                                          [Atomic Transaction]
                                                                    │
                                                                    ├─ Calculate Points
                                                                    ├─ Create Transaction
                                                                    ├─ Update User Points
                                                                    └─ All succeed? ──► Success 201
                                                                       Any fails? ────► Rollback
```

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd recycling
   ```

2. **Create and activate virtual environment (recommended):**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate (Windows)
   venv\Scripts\activate
   
   # Activate (Linux/Mac)
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the API:**
   - Base URL: `http://127.0.0.1:8000/api/`
---

## API Documentation

### Base URL
```
http://127.0.0.1:8000/api/
```

### 1. Register User

Register a new user or create an account.

**Endpoint:** `POST /api/register/`

**Request Body:**
```json
{
  "name": "Alice",
  "phone": "12345678901"
}
```

**Success Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Alice",
  "phone": "12345678901",
  "points": 0,
  "is_active": true
}
```

**Error Responses:**
- `400 Bad Request` - Missing or invalid phone/name
  ```json
  {
    "error": "Phone number is required.",
    "field": "phone"
  }
  ```

**cURL Example:**
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "phone": "12345678901"}'
```

---

### 2. Create Recycling Transaction

Record a recycling transaction and award points to the user.

**Endpoint:** `POST /api/recycle/`

**Request Body:**
```json
{
  "user_id": 1,
  "material_type": "plastic",
  "quantity": 3
}
```

**Success Response:** `201 Created`
```json
{
  "message": "Recycling transaction recorded.",
  "transaction": {
    "id": 1,
    "user_id": 1,
    "material_type": "plastic",
    "quantity": 3,
    "points_awarded": 15,
    "timestamp": "2026-01-14T01:23:45.678Z"
  }
}
```

**Error Responses:**

- `400 Bad Request` - Invalid user
  ```json
  {
    "user_id": ["User does not exist or is inactive."]
  }
  ```

- `400 Bad Request` - Invalid material type
  ```json
  {
    "material_type": ["Invalid material. Allowed: ['plastic', 'can']"]
  }
  ```

- `400 Bad Request` - Invalid quantity
  ```json
  {
    "quantity": ["Quantity must be a positive integer."]
  }
  ```

- `400 Bad Request` - Duplicate scan detected
  ```json
  {
    "duplicate": ["Duplicate scan detected. Please wait at least 5 seconds between recycling the same material."]
  }
  ```

**cURL Example:**
```bash
curl -X POST http://127.0.0.1:8000/api/recycle/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "material_type": "plastic", "quantity": 3}'
```

---

### 3. Get User Points

Retrieve a user's profile and current points balance.

**Endpoint:** `GET /api/users/<user_id>/`

**URL Parameters:**
- `user_id` (integer) - The unique ID of the user

**Success Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Alice",
  "phone": "12345678901",
  "points": 15,
  "is_active": true
}
```

**Error Responses:**
- `404 Not Found` - User not found or inactive
  ```json
  {
    "error": "User not found or inactive."
  }
  ```

**cURL Example:**
```bash
curl http://127.0.0.1:8000/api/users/1/
```

---

## Database Schema

### User Model

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto | Unique user identifier |
| `name` | CharField(80) | Required | User's full name |
| `phone` | CharField(11) | Required | Phone number (11 digits, not unique) |
| `points` | Integer | Default: 0 | Total accumulated points |
| `is_active` | Boolean | Default: True | Soft delete flag |

### RecyclingTransaction Model

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto | Unique transaction identifier |
| `user` | ForeignKey | Required, CASCADE | Reference to User |
| `material_type` | CharField(20) | Choices: plastic/can | Type of material recycled |
| `quantity` | PositiveInteger | Required | Number of items recycled |
| `points_awarded` | PositiveInteger | Required | Points awarded for this transaction |
| `timestamp` | DateTime | Auto | Transaction creation time |

### Database Indexes

- `RecyclingTransaction.user` - Indexed for user queries
- `RecyclingTransaction.material_type` - Indexed for material filtering
- `RecyclingTransaction.timestamp` - Indexed for time-based queries
- Composite index: `[user, material_type, -timestamp]` - Optimizes duplicate scan checks

---

## Business Rules

### Points Calculation

Points are calculated based on material type and quantity:

```
points = quantity × POINT_RULES[material_type]
```

**Point Rules:**
- **Plastic:** 5 points per item
- **Can:** 10 points per item

**Example:**
- 3 plastic items = 3 × 5 = **15 points**
- 2 cans = 2 × 10 = **20 points**

### Duplicate Scan Prevention

To prevent fraud and accidental duplicate submissions:

- **Rule:** Same user cannot recycle the same material type within 5 seconds
- **Window:** Configurable via `DUPLICATE_SCAN_WINDOW_SECONDS` in `constants.py`
- **Enforcement:** Checked inside atomic transaction to prevent race conditions
- **Response:** Returns `400 Bad Request` with duplicate error message

### Transaction Atomicity

All recycling transactions are atomic:
- Transaction record creation
- User points update
- Both succeed or both fail (rollback)

This ensures data consistency and prevents partial updates.

---

## Assumptions & Trade-offs

### Assumptions

1. **Phone Numbers:** Multiple users can have the same phone number (not unique)
2. **Material Types:** Only two types supported: "plastic" and "can"
3. **User Identification:** Users identified by unique `id`, not phone number
4. **Duplicate Window:** 5-second window for duplicate prevention (configurable)
5. **Soft Deletes:** `is_active` field supports soft deletion
6. **No Authentication:** Simplified demo without authentication/authorization
7. **Database:** SQLite for development (can switch to PostgreSQL for production)

### Trade-offs

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| SQLite | Limited concurrency | Simple setup for demo, easy to switch to PostgreSQL |
| No Auth | Security risk | Simplifies demo, focus on core flow |
| Phone not unique | Cannot identify by phone | Allows shared devices/family accounts |
| 5-second duplicate window | May block legitimate rapid scans | Prevents fraud and accidental duplicates |
| Atomic transactions | Slight performance overhead | Ensures data integrity |

---

## Project Structure

```
recycling/
│
├── main/                          # Main application
│   ├── models.py                  # Database models (User, RecyclingTransaction)
│   ├── views.py                   # API view classes
│   ├── serializers.py             # Request/response serialization & validation
│   ├── urls.py                    # URL routing
│   ├── rules.py                   # Points calculation logic
│   ├── constants.py               # Configuration constants
│   ├── admin.py                   # Django admin configuration
│   ├── apps.py                    # App configuration
│   └── migrations/                 # Database migrations
│     
│
├── recycling/                     # Django project settings
│   ├── settings.py                # Django configuration
│   ├── urls.py                    # Root URL configuration
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
│
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── db.sqlite3                     # SQLite database (development)
└── readme.md                      # This file
```

### Key Files Explained

- **`models.py`**: Defines User and RecyclingTransaction database models
- **`views.py`**: API endpoints (RegisterUserView, RecyclingTransactionView, UserPointsView)
- **`serializers.py`**: Handles validation, transformation, and business logic
- **`rules.py`**: Centralized points calculation (`POINT_RULES`, `calculate_points()`)
- **`constants.py`**: Configuration values (`DUPLICATE_SCAN_WINDOW_SECONDS`, `PHONE_LENGTH`)
- **`urls.py`**: Maps URLs to view classes

---

## Technical Highlights

### Data Integrity
- ✅ Atomic database transactions prevent partial updates
- ✅ `select_for_update()` prevents race conditions
- ✅ Duplicate check inside transaction prevents concurrent duplicates

### Performance
- ✅ Database indexes on frequently queried fields
- ✅ Composite index for duplicate scan queries
- ✅ Efficient query patterns

### Code Quality
- ✅ Clear separation of concerns (MVC pattern)
- ✅ Centralized business logic (rules.py, constants.py)
- ✅ Comprehensive input validation
- ✅ Standardized error responses
- ✅ Type hints and documentation

### Security Considerations
- ✅ Input validation prevents invalid data
- ✅ Duplicate scan prevention reduces fraud
- ✅ Atomic transactions prevent data corruption
- No authentication (simplified for demo)

---

## Sample API Workflow

### Complete User Journey

```bash
# 1. Register a new user
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "phone": "12345678901"}'

# Response: {"id": 1, "name": "Alice", "phone": "12345678901", "points": 0, "is_active": true}

# 2. Recycle 3 plastic items
curl -X POST http://127.0.0.1:8000/api/recycle/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "material_type": "plastic", "quantity": 3}'

# Response: {"message": "Recycling transaction recorded.", "transaction": {...}, "points_awarded": 15}

# 3. Check user points
curl http://127.0.0.1:8000/api/users/1/

# Response: {"id": 1, "name": "Alice", "phone": "12345678901", "points": 15, "is_active": true}

# 4. Recycle 2 cans
curl -X POST http://127.0.0.1:8000/api/recycle/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "material_type": "can", "quantity": 2}'

# Response: {"message": "Recycling transaction recorded.", "transaction": {...}, "points_awarded": 20}

# 5. Check updated points (should be 35)
curl http://127.0.0.1:8000/api/users/1/

# Response: {"id": 1, "name": "Alice", "phone": "12345678901", "points": 35, "is_active": true}
```

---

## Conclusion

This project demonstrates:

- ✅ **System thinking & backend architecture** - Clean, scalable design
- ✅ **Clean API design & validation** - RESTful endpoints with proper error handling
- ✅ **Practical business rule enforcement** - Duplicate prevention, points calculation
- ✅ **Structured error handling** - Consistent error responses
- ✅ **Data integrity** - Atomic transactions, race condition prevention
- ✅ **Clear documentation** - Comprehensive setup and usage instructions

---

## License

This project is part of a coding challenge for Drop Me.

---

## Contact & Support

For questions or issues, please refer to the project repository or contact me.
