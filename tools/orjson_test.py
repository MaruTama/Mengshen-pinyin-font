import os
import orjson

TAMPLATE_GLYF_JSON     = os.path.join("./tmp/json", "template_glyf.json")
TAMPLATE_GLYF_OUT_JSON = os.path.join("./tmp/json", "template_glyf_out.json")


if __name__ == "__main__":
    # binary mode
    with open(TAMPLATE_GLYF_JSON, "rb") as f:
        glyf = orjson.loads(f.read())
        print(glyf["cid07316"])

    with open(TAMPLATE_GLYF_OUT_JSON, "wb") as f:
        serialized_glyf = orjson.dumps(glyf, option=orjson.OPT_INDENT_2)
        f.write(serialized_glyf)
