ALTER TABLE reserva
    ADD COLUMN IF NOT EXISTS encuesta_enviada BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS encuesta_enviada_fecha TIMESTAMP;

CREATE TABLE IF NOT EXISTS resena_paquete (
    id_resena             SERIAL PRIMARY KEY,
    id_paquete            INT NOT NULL REFERENCES paquete_turistico(id_paquete) ON DELETE CASCADE,
    id_cliente            INT NOT NULL REFERENCES cliente(id_cliente)          ON DELETE CASCADE,
    id_reserva            INT REFERENCES reserva(id_reserva)                  ON DELETE SET NULL,
    calificacion          SMALLINT,
    calificacion_servicio SMALLINT,
    titulo                VARCHAR(120),
    comentario            TEXT,
    fecha_resena          TIMESTAMP NOT NULL DEFAULT NOW(),
    estado                VARCHAR(20) NOT NULL DEFAULT 'visible',
    origen                VARCHAR(20) NOT NULL DEFAULT 'real',
    CONSTRAINT chk_resena_calificacion CHECK (calificacion BETWEEN 1 AND 5),
    CONSTRAINT chk_resena_servicio CHECK (
        calificacion_servicio IS NULL OR calificacion_servicio BETWEEN 1 AND 5
    ),
    CONSTRAINT chk_resena_estado CHECK (estado IN ('visible', 'oculta', 'pendiente')),
    CONSTRAINT chk_resena_origen CHECK (origen IN ('real', 'semilla'))
);

ALTER TABLE resena_paquete
    ADD COLUMN IF NOT EXISTS origen VARCHAR(20) NOT NULL DEFAULT 'real';

UPDATE resena_paquete
SET origen = 'real'
WHERE origen IS NULL;

ALTER TABLE resena_paquete ALTER COLUMN origen SET NOT NULL;
ALTER TABLE resena_paquete ALTER COLUMN calificacion DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_resena_calificacion'
          AND conrelid = 'resena_paquete'::regclass
    ) THEN
        ALTER TABLE resena_paquete
            ADD CONSTRAINT chk_resena_calificacion CHECK (calificacion BETWEEN 1 AND 5);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_resena_servicio'
          AND conrelid = 'resena_paquete'::regclass
    ) THEN
        ALTER TABLE resena_paquete
            ADD CONSTRAINT chk_resena_servicio CHECK (
                calificacion_servicio IS NULL OR calificacion_servicio BETWEEN 1 AND 5
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_resena_estado'
          AND conrelid = 'resena_paquete'::regclass
    ) THEN
        ALTER TABLE resena_paquete
            ADD CONSTRAINT chk_resena_estado CHECK (
                estado IN ('visible', 'oculta', 'pendiente')
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_resena_origen'
          AND conrelid = 'resena_paquete'::regclass
    ) THEN
        ALTER TABLE resena_paquete
            ADD CONSTRAINT chk_resena_origen CHECK (origen IN ('real', 'semilla'));
    END IF;
END $$;

ALTER TABLE resena_paquete DROP CONSTRAINT IF EXISTS uq_resena_paquete_cliente;
ALTER TABLE resena_paquete DROP CONSTRAINT IF EXISTS uq_resena_reserva;

DROP INDEX IF EXISTS uq_resena_real_cliente;

CREATE UNIQUE INDEX IF NOT EXISTS uq_resena_real_reserva
    ON resena_paquete (id_reserva)
    WHERE origen = 'real' AND id_reserva IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_resena_paquete_visible
    ON resena_paquete (id_paquete, estado);

CREATE INDEX IF NOT EXISTS idx_resena_paquete_origen
    ON resena_paquete (origen, id_paquete);

CREATE INDEX IF NOT EXISTS idx_reserva_encuesta_pendiente
    ON reserva (estado, encuesta_enviada, fecha_viaje);

WITH paquetes AS (
    SELECT
        id_paquete,
        ROW_NUMBER() OVER (ORDER BY id_paquete) - 1 AS n
    FROM paquete_turistico
),
clientes AS (
    SELECT
        id_cliente,
        ROW_NUMBER() OVER (ORDER BY id_cliente) - 1 AS n
    FROM cliente
),
plantillas AS (
    VALUES
        (0, 5, 5, 'Excelente recorrido', 'Guía atento, paisajes increíbles y muy buena organización.'),
        (1, 4, 5, 'Muy buena experiencia', 'Todo funcionó según lo previsto; repetiría sin dudarlo.'),
        (2, 3, 4, 'Buena pero mejorable', 'El alojamiento cumplió; las comidas podrían mejorar.'),
        (3, 2, 3, 'No cumplió expectativas', 'Hubo demasiada espera en el transporte.'),
        (4, 5, 4, 'Inolvidable', 'Las actividades fueron excelentes y el equipo muy amable.'),
        (5, 1, 2, 'No lo recomiendo', 'Cancelaron una actividad sin avisar y hubo poca información.'),
        (6, 4, 4, 'Muy recomendable', 'Buena relación precio/calidad, con detalles muy cuidados.'),
        (7, 5, 5, 'Superó mis expectativas', 'Atención excelente del proveedor y del guía durante todo el viaje.')
),
semilla AS (
    SELECT
        p.id_paquete,
        c.id_cliente,
        t.column2 AS calificacion,
        t.column3 AS calificacion_servicio,
        t.column4 AS titulo,
        t.column5 AS comentario,
        NOW() - make_interval(days => (p.n * 3)::int) AS fecha_resena
    FROM paquetes p
    JOIN plantillas t ON t.column1 = (p.n % 8)
    JOIN clientes c ON c.n = t.column1
    WHERE p.n < 20
)
INSERT INTO resena_paquete (
    id_paquete,
    id_cliente,
    calificacion,
    calificacion_servicio,
    titulo,
    comentario,
    fecha_resena,
    estado,
    origen
)
SELECT
    s.id_paquete,
    s.id_cliente,
    s.calificacion,
    s.calificacion_servicio,
    s.titulo,
    s.comentario,
    s.fecha_resena,
    'visible',
    'semilla'
FROM semilla s
WHERE NOT EXISTS (
    SELECT 1
    FROM resena_paquete rp
    WHERE rp.id_paquete = s.id_paquete
      AND rp.id_cliente = s.id_cliente
      AND rp.origen = 'semilla'
);

INSERT INTO reserva (
    codigo_unico,
    fecha_reserva,
    fecha_viaje,
    estado,
    cant_adultos,
    cant_menores,
    acepta_no_reembolso,
    id_cliente,
    id_paquete,
    mascotas,
    encuesta_enviada,
    encuesta_enviada_fecha
)
SELECT
    'MRV-ENCUESTA-DEMO',
    CURRENT_DATE,
    CURRENT_DATE - INTERVAL '2 days',
    'completada',
    1,
    0,
    TRUE,
    c.id_cliente,
    (SELECT id_paquete FROM paquete_turistico ORDER BY id_paquete LIMIT 1),
    FALSE,
    TRUE,
    NOW()
FROM cliente c
WHERE c.correo = 'nicollvaleria.sabogal.9@gmail.com'
  AND NOT EXISTS (
      SELECT 1
      FROM reserva r
      WHERE r.codigo_unico = 'MRV-ENCUESTA-DEMO'
  );
