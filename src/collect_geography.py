import pandas as pd
from geobr import read_municipal_seat

from .settings import DATA_RAW, UF

def main():
    # A sede municipal é usada como ponto representativo da exposição meteorológica.
    # Isso é mais coerente para exposição populacional do que o centro geométrico
    # de municípios amazônicos muito extensos e pouco povoados.
    gdf = read_municipal_seat(year=2022, code_muni=UF)

    if gdf.empty:
        raise RuntimeError("O geobr não retornou sedes municipais do Amazonas.")

    if gdf.crs is not None and str(gdf.crs).lower() not in {"epsg:4326", "wgs84"}:
        gdf = gdf.to_crs(4326)

    geom_col = gdf.geometry.name
    out = pd.DataFrame({
        "id_municipio": gdf["code_muni"].astype("Int64").astype(str).str.zfill(7),
        "municipio": gdf["name_muni"].astype(str),
        "latitude": gdf[geom_col].y,
        "longitude": gdf[geom_col].x,
    })
    out["id_municipio_6"] = out["id_municipio"].str[:6]
    out = out.sort_values("id_municipio").drop_duplicates("id_municipio")

    if len(out) != 62:
        raise RuntimeError(
            f"Esperados 62 municípios; geobr retornou {len(out)}. "
            "Verifique a versão da malha antes de continuar."
        )

    out.to_csv(DATA_RAW / "municipios_am_sedes.csv", index=False)
    print(f"{len(out)} sedes municipais salvas.")

if __name__ == "__main__":
    main()
