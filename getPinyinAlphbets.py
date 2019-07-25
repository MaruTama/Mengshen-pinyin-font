import os
import glob


# 漢字のSVGがあるディレクトリ
DIR_SVG = "./fonts/SVGs"

if __name__ == '__main__':
    files = glob.glob(os.path.join(DIR_SVG,"*"))
    # 全てのファイル名のセットを作る
    file_names = {os.path.basename(file) for file in files}

    dict_pinyin_alphbets = {"A.svg":"a.svg","Amacron.svg":"ā.svg","Aacute.svg":"á.svg","uni01CE.svg":"ǎ.svg","Agrave.svg":"à.svg","B.svg":"b.svg","C.svg":"c.svg","D.svg":"d.svg","E.svg":"e.svg","Emacron.svg":"ē.svg","Eacute.svg":"é.svg","Ecaron.svg":"ě.svg","Egrave.svg":"è.svg","F.svg":"f.svg","G.svg":"g.svg","H.svg":"h.svg","I.svg":"i.svg","Imacron.svg":"ī.svg","Iacute.svg":"í.svg","uni01D0.svg":"ǐ.svg","Igrave.svg":"ì.svg","J.svg":"j.svg","K.svg":"k.svg","L.svg":"l.svg","M.svg":"m.svg","N.svg":"n.svg","O.svg":"o.svg","Omacron.svg":"ō.svg","Oacute.svg":"ó.svg","uni01D2.svg":"ǒ.svg","Ograve.svg":"ò.svg","P.svg":"p.svg","Q.svg":"q.svg","R.svg":"r.svg","S.svg":"s.svg","T.svg":"t.svg","U.svg":"u.svg","Umacron.svg":"ū.svg","Uacute.svg":"ú.svg","uni01D4.svg":"ǔ.svg","Ugrave.svg":"ù.svg","Udieresis.svg":"ü.svg","V.svg":"v.svg","W.svg":"w.svg","X.svg":"x.svg","Y.svg":"y.svg","Z.svg":"z.svg","uni01D6.svg":"ǖ.svg","uni01D8.svg":"ǘ.svg","uni01DA.svg":"ǚ.svg","uni01DC.svg":"ǜ.svg","uni1E3F.svg":"ḿ.svg","Nacute.svg":"ń.svg","uni1EDF.svg":"ở.svg"}

    # 漢字以外のファイルを消す
    for file_name in file_names:
        try:
            if file_name in dict_pinyin_alphbets:
                print(file_name)
                os.rename(os.path.join(DIR_SVG,file_name), os.path.join(DIR_SVG,dict_pinyin_alphbets[file_name]))
            else:
                os.remove(os.path.join(DIR_SVG,file_name))

        except Exception as e:
            pass
