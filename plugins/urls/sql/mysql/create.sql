CREATE TABLE IF NOT EXISTS urls (
  id INT NOT NULL auto_increment,
  url TEXT NOT NULL,
  submitted TIMESTAMP(14) NOT NULL,
  username VARCHAR(256) NOT NULL,
  target VARCHAR(256) NOT NULL,
  protocol VARCHAR(256) NOT NULL
)