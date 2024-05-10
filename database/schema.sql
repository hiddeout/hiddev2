CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- This script creates necessary tables for the jail cog

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
