-- FTS5 миграция для поиска по местам
-- Создание виртуальной таблицы для полнотекстового поиска

-- Создаем FTS5 виртуальную таблицу
-- content='places' указывает на основную таблицу
-- content_rowid='id' связывает с первичным ключом основной таблицы
CREATE VIRTUAL TABLE IF NOT EXISTS places_fts USING fts5(
    title,           -- название места
    description,     -- описание
    tags,           -- теги (JSON массив)
    flags,          -- флаги (JSON массив)
    city,           -- город
    address,        -- адрес
    content='places', content_rowid='id'
);

-- Триггер для INSERT - добавляет запись в FTS таблицу
CREATE TRIGGER IF NOT EXISTS places_fts_insert AFTER INSERT ON places BEGIN
    INSERT INTO places_fts(rowid, title, description, tags, flags, city, address) 
    VALUES (NEW.id, NEW.name, NEW.description, NEW.tags, NEW.flags, NEW.city, NEW.address);
END;

-- Триггер для UPDATE - обновляет запись в FTS таблице
CREATE TRIGGER IF NOT EXISTS places_fts_update AFTER UPDATE ON places BEGIN
    INSERT INTO places_fts(places_fts, rowid, title, description, tags, flags, city, address) 
    VALUES('delete', OLD.id, OLD.name, OLD.description, OLD.tags, OLD.flags, OLD.city, OLD.address);
    INSERT INTO places_fts(rowid, title, description, tags, flags, city, address) 
    VALUES (NEW.id, NEW.name, NEW.description, NEW.tags, NEW.flags, NEW.city, NEW.address);
END;

-- Триггер для DELETE - удаляет запись из FTS таблицы
CREATE TRIGGER IF NOT EXISTS places_fts_delete AFTER DELETE ON places BEGIN
    INSERT INTO places_fts(places_fts, rowid, title, description, tags, flags, city, address) 
    VALUES('delete', OLD.id, OLD.name, OLD.description, OLD.tags, OLD.flags, OLD.city, OLD.address);
END;

-- Создаем индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_places_fts_title ON places_fts(title);
CREATE INDEX IF NOT EXISTS idx_places_fts_city ON places_fts(city);

-- Комментарий: FTS5 автоматически создает внутренние индексы для поиска
