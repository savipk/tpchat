PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- USERS
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  identifier TEXT NOT NULL UNIQUE,
  createdAt TEXT NOT NULL,      -- ISO8601 string
  metadata TEXT                 -- JSON as TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_identifier ON users(identifier);

-- THREADS
CREATE TABLE IF NOT EXISTS threads (
  id TEXT PRIMARY KEY,
  userId TEXT NOT NULL,
  userIdentifier TEXT,          -- required by data layer queries
  name TEXT,
  createdAt TEXT NOT NULL,
  metadata TEXT,                -- JSON as TEXT
  tags TEXT,                    -- required by data layer queries
  FOREIGN KEY (userId) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(userId, createdAt);

-- STEPS (messages / tool steps)
CREATE TABLE IF NOT EXISTS steps (
  id TEXT PRIMARY KEY,
  name TEXT,
  type TEXT,                    -- "user", "assistant", "tool", etc.
  threadId TEXT NOT NULL,
  parentId TEXT,                -- NEW: link nested steps
  streaming BOOLEAN DEFAULT 0,
  waitForAnswer BOOLEAN DEFAULT 0,
  isError BOOLEAN DEFAULT 0,
  metadata TEXT,                -- JSON as TEXT
  tags TEXT,
  input TEXT,
  output TEXT,
  createdAt TEXT NOT NULL,
  start TEXT,
  end TEXT,
  generation TEXT,
  showInput BOOLEAN DEFAULT 1,
  language TEXT,
  FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE,
  FOREIGN KEY (parentId) REFERENCES steps(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_steps_thread ON steps(threadId, createdAt);
CREATE INDEX IF NOT EXISTS idx_steps_parent ON steps(parentId);

-- ELEMENTS (files, images, audio, etc.)
CREATE TABLE IF NOT EXISTS elements (
  id TEXT PRIMARY KEY,
  threadId TEXT NOT NULL,
  type TEXT,                    -- "image", "file", "audio", etc.
  chainlitKey TEXT,             -- NEW: internal key used by Chainlit
  url TEXT,                     -- remote URL if any
  objectKey TEXT,               -- NEW: for cloud object storage references
  name TEXT,
  display TEXT,
  size TEXT,
  language TEXT,
  page TEXT,
  forId TEXT,                   -- NEW: link to step
  mime TEXT,
  props TEXT,                   -- JSON
  FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE,
  FOREIGN KEY (forId) REFERENCES steps(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_elements_thread ON elements(threadId);
CREATE INDEX IF NOT EXISTS idx_elements_forid ON elements(forId);

-- FEEDBACKS (ratings/comments)
CREATE TABLE IF NOT EXISTS feedbacks (
  id TEXT PRIMARY KEY,
  forId TEXT NOT NULL,          -- renamed from stepId for Chainlit >=1.1
  userId TEXT,
  value REAL,
  comment TEXT,
  createdAt TEXT NOT NULL,
  metadata TEXT,                -- JSON as TEXT
  FOREIGN KEY (forId) REFERENCES steps(id) ON DELETE CASCADE,
  FOREIGN KEY (userId) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_feedbacks_forid ON feedbacks(forId);

COMMIT;
