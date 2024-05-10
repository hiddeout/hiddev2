-- This script creates necessary tables for the warnings and jail functionality

-- Table for warnings
CREATE TABLE IF NOT EXISTS warns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  server_id INTEGER NOT NULL,
  moderator_id INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for jail settings
CREATE TABLE IF NOT EXISTS setme (
  channel_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  guild_id INTEGER NOT NULL,
  PRIMARY KEY (guild_id)
);

-- Table for jailed members
CREATE TABLE IF NOT EXISTS jail (
  guild_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  roles TEXT NOT NULL,
  PRIMARY KEY (user_id, guild_id)
);

-- Table for AFK settings
CREATE TABLE IF NOT EXISTS afk (
  guild_id INTEGER,
  user_id INTEGER,
  reason TEXT,
  afk_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (guild_id, user_id)
);
