-- Ejecutar en Supabase → SQL Editor
-- GSPresupuestos: perfiles, condiciones y ofertas

-- Perfil de cada usuario (logo, pie, datos empresa)
CREATE TABLE IF NOT EXISTS perfiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre_empresa TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    email_empresa TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    cif TEXT DEFAULT '',
    pie_texto TEXT DEFAULT '',
    logo_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hasta 3 plantillas de condiciones por usuario
CREATE TABLE IF NOT EXISTS condiciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL DEFAULT 'Condiciones',
    contenido TEXT DEFAULT '',
    orden INT NOT NULL DEFAULT 1 CHECK (orden BETWEEN 1 AND 3),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, orden)
);

-- Ofertas guardadas
CREATE TABLE IF NOT EXISTS ofertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL DEFAULT 'Sin nombre',
    num_oferta TEXT DEFAULT '',
    cliente TEXT DEFAULT '',
    datos JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE condiciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE ofertas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "perfiles_own" ON perfiles FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "condiciones_own" ON condiciones FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "ofertas_own" ON ofertas FOR ALL USING (auth.uid() = user_id);

-- Bucket para logos: crear en Storage → New bucket → nombre "logos" → Public bucket

INSERT INTO storage.buckets (id, name, public)
VALUES ('logos', 'logos', true)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "logos_public_read" ON storage.objects
    FOR SELECT USING (bucket_id = 'logos');

CREATE POLICY "logos_auth_upload" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'logos' AND auth.role() = 'authenticated'
    );

CREATE POLICY "logos_auth_update" ON storage.objects
    FOR UPDATE USING (bucket_id = 'logos' AND auth.role() = 'authenticated');

-- Perfil vacío al registrarse un usuario nuevo
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.perfiles (user_id) VALUES (NEW.id);
    INSERT INTO public.condiciones (user_id, nombre, orden) VALUES
        (NEW.id, 'Condiciones 1', 1),
        (NEW.id, 'Condiciones 2', 2),
        (NEW.id, 'Condiciones 3', 3);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
