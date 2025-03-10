-- Create the customs_data table if it does not exist
CREATE TABLE IF NOT EXISTS customs_data (
    id SERIAL PRIMARY KEY,
    "Час оформлення" TIMESTAMP,
    "Назва ПМО" TEXT,
    "Тип" TEXT,
    "Номер МД" TEXT,
    "Дата" TIMESTAMP,
    "Відправник" TEXT,
    "ЕДРПОУ" BIGINT,
    "Одержувач" TEXT,
    "№" INT,
    "Код товару" TEXT,
    "Опис товару" TEXT,
    "Кр.торг." TEXT,
    "Кр.відпр." TEXT,
    "Кр.пох." TEXT,
    "Умови пост." TEXT,
    "Місце пост" TEXT,
    "К-ть" DOUBLE PRECISION,
    "Один.вим." INT,
    "Брутто, кг." DOUBLE PRECISION,
    "Нетто, кг." DOUBLE PRECISION,
    "Вага по МД" DOUBLE PRECISION,
    "ФВ вал.контр" DOUBLE PRECISION,
    "Особ.перем." TEXT,
    "43" INT,
    "43_01" INT,
    "РФВ Дол/кг." DOUBLE PRECISION,
    "Вага.один." DOUBLE PRECISION,
    "Вага різн." DOUBLE PRECISION,
    "Контракт" TEXT,
    "3001" INT,
    "3002" INT,
    "9610" INT,
    "Торг.марк." TEXT,
    "РМВ Нетто Дол/кг." DOUBLE PRECISION,
    "РМВ Дол/дод.од." DOUBLE PRECISION,
    "РМВ Брутто Дол/кг" DOUBLE PRECISION,
    "Призн.Зед" INT,
    "Мін.База Дол/кг." DOUBLE PRECISION,
    "Різн.мін.база" DOUBLE PRECISION,
    "КЗ Нетто Дол/кг." DOUBLE PRECISION,
    "КЗ Дол/шт." DOUBLE PRECISION,
    "Різн.КЗ Дол/кг" DOUBLE PRECISION,
    "Різ.КЗ Дол/шт" DOUBLE PRECISION,
    "КЗ Брутто Дол/кг." DOUBLE PRECISION,
    "Різ.КЗ Брутто" DOUBLE PRECISION,
    "пільгова" DOUBLE PRECISION,
    "повна" TEXT
);

-- Create the query_log table if it does not exist
CREATE TABLE IF NOT EXISTS query_log (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster querying
CREATE INDEX IF NOT EXISTS idx_customs_data_date ON customs_data ("Дата");
CREATE INDEX IF NOT EXISTS idx_customs_data_sender ON customs_data ("Відправник");
CREATE INDEX IF NOT EXISTS idx_customs_data_receiver ON customs_data ("Одержувач");
CREATE INDEX IF NOT EXISTS idx_customs_data_product_code ON customs_data ("Код товару");
CREATE INDEX IF NOT EXISTS idx_query_log_timestamp ON query_log (timestamp);

-- Migration for existing data - update field types if the table already exists
DO $$
BEGIN
    -- Check if the table exists and if the columns have the wrong types
    IF EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'customs_data' 
        AND column_name = 'пільгова' 
        AND data_type = 'integer'
    ) THEN
        ALTER TABLE customs_data 
        ALTER COLUMN "пільгова" TYPE DOUBLE PRECISION USING CASE 
            WHEN "пільгова" IS NULL THEN NULL 
            ELSE "пільгова"::DOUBLE PRECISION 
        END;
    END IF;

    IF EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'customs_data' 
        AND column_name = 'повна' 
        AND data_type = 'integer'
    ) THEN
        ALTER TABLE customs_data 
        ALTER COLUMN "повна" TYPE TEXT USING CASE 
            WHEN "повна" IS NULL THEN NULL 
            ELSE "повна"::TEXT 
        END;
    END IF;
END $$;