"""
Seed Data — ALL 80 rules + 15 sample products
Run: POST http://localhost:8000/seed
"""
 
def r(id,name,field,values,actions_str):
    """Helper to build a rule from compact string"""
    actions=[]
    for a in actions_str.split(","):
        p=a.split(":")
        actions.append({"attr":p[0],"value":p[1],"score":float(p[2])})
    return {"id":id,"name":name,"isActive":True,"priority":5 if field=="bodyType" else 3 if field in["skinTone","occasion"] else 2,
            "conditions":{"operator":"AND","clauses":[{"field":field,"op":"IN","values":values}]},"actions":actions}
 
SEED_RULES = [
    # ══════════════════════════════════════════
    # BODY TYPE RULES (13)
    # ══════════════════════════════════════════
    r("BT01","Pear","bodyType",["pear"],"fit:a_line:2,fit:structured:1.5,fit:wrap:1.5,neckline:boat:2,neckline:off_shoulder:2,sleeve:puff:2,sleeve:bell:1.5,waistline:high:2,waistline:belted:1.5,silhouette:fitted_top_flared_bottom:2.5,length:knee:1.5,length:midi:1.5,fit:bodycon:-2.5,fit:slim:-1.5,length:mini:-1.5,waistline:low:-2,neckline:turtle:-1.5"),
    r("BT02","Apple","bodyType",["apple"],"neckline:v_neck:2,neckline:scoop:1.5,fit:relaxed:1.5,fit:wrap:1.5,fit:a_line:1.5,waistline:empire:2,palette:monochrome:1,fit:bodycon:-2.5,neckline:turtle:-1.5,waistline:low:-2"),
    r("BT03","Hourglass","bodyType",["hourglass"],"fit:tailored:2,fit:bodycon:2,fit:wrap:2,waistline:high:2,waistline:belted:2,neckline:v_neck:1.5,neckline:sweetheart:1.5,silhouette:hourglass_silhouette:2.5,silhouette:x_line:2,fit:oversized:-2,fit:boxy:-2,fit:shift:-2,waistline:drop:-1.5"),
    r("BT04","Rectangle","bodyType",["rectangle"],"fit:wrap:2,fit:peplum:1.5,fit:a_line:1.5,waistline:belted:2.5,waistline:high:1.5,waistline:empire:1.5,sleeve:puff:1.5,neckline:sweetheart:1,silhouette:x_line:2,fit:shift:-1.5"),
    r("BT05","Inverted triangle","bodyType",["inverted_triangle"],"neckline:v_neck:2,neckline:scoop:1.5,fit:flared:2,fit:a_line:1.5,fit:relaxed:1,length:midi:1,neckline:boat:-2,neckline:off_shoulder:-2,sleeve:puff:-2,fit:structured:-1"),
    r("BT06","Oval","bodyType",["oval"],"neckline:v_neck:2,fit:a_line:2,fit:relaxed:1.5,fit:wrap:1.5,waistline:empire:2,palette:monochrome:1.5,pattern:vertical_stripes:1.5,fit:bodycon:-3,length:crop:-2.5,pattern:horizontal_stripes:-2,waistline:low:-2"),
    r("BT07","Athletic","bodyType",["athletic"],"fit:wrap:2,fit:a_line:1.5,neckline:off_shoulder:1.5,fabric:silk:1.5,pattern:floral:1.5,sleeve:bell:1,waistline:belted:1.5,fit:boxy:-1.5"),
    r("BT08","Petite curvy","bodyType",["petite_curvy"],"fit:tailored:2,fit:wrap:2,waistline:high:2.5,length:above_knee:1.5,length:knee:1.5,silhouette:x_line:2,neckline:v_neck:1.5,palette:monochrome:1,fit:oversized:-2.5,length:maxi:-1.5,fit:boxy:-2"),
    r("BT09","Tall slim","bodyType",["tall_slim"],"fit:relaxed:1.5,fit:oversized:1,fit:wrap:1.5,length:maxi:2,length:midi:1.5,waistline:belted:2,sleeve:puff:1.5,pattern:horizontal_stripes:1,silhouette:layered:1.5"),
    r("BT10","Plus size","bodyType",["plus_size"],"fit:structured:2,fit:a_line:2,fit:wrap:2,neckline:v_neck:2,waistline:high:2,waistline:empire:1.5,silhouette:x_line:2,palette:dark:1,pattern:vertical_stripes:1.5,fit:bodycon:-2,fit:boxy:-1.5,pattern:horizontal_stripes:-1.5,length:crop:-2"),
    r("BT11","Lean","bodyType",["lean"],"fit:tailored:1.5,fit:structured:1.5,sleeve:puff:1.5,pattern:horizontal_stripes:1.5,waistline:belted:2,silhouette:x_line:2,neckline:boat:1.5,fit:oversized:-1"),
    r("BT12","Stocky","bodyType",["stocky"],"neckline:v_neck:2,fit:structured:1.5,fit:tailored:1.5,palette:monochrome:1.5,pattern:vertical_stripes:1.5,silhouette:column:1.5,fit:oversized:-2,pattern:horizontal_stripes:-1.5,fit:boxy:-2"),
    r("BT13","Broad","bodyType",["broad"],"neckline:v_neck:2,neckline:scoop:1.5,fit:tailored:1.5,palette:dark:1,silhouette:column:1.5,pattern:vertical_stripes:1,neckline:boat:-2,sleeve:puff:-1.5,fit:oversized:-1.5"),
 
    # ══════════════════════════════════════════
    # SKIN TONE RULES (11)
    # ══════════════════════════════════════════
    r("SK01","Porcelain","skinTone",["porcelain"],"colorFamily:navy:2,colorFamily:emerald:1.5,colorFamily:lavender:1.5,colorFamily:blush:1.5,palette:jewel:1.5,palette:cool:1.5,colorFamily:mustard:-1.5,palette:neon:-1.5"),
    r("SK02","Fair","skinTone",["fair"],"colorFamily:pink:1.5,colorFamily:lavender:1.5,colorFamily:navy:1.5,colorFamily:burgundy:1.5,palette:pastel:1.5,palette:jewel:1,palette:neon:-1.5"),
    r("SK03","Light","skinTone",["light"],"colorFamily:coral:1.5,colorFamily:teal:1.5,colorFamily:plum:1.5,palette:jewel:1.5,colorFamily:sage:1,palette:neon:-1"),
    r("SK04","Medium","skinTone",["medium"],"colorFamily:teal:2,colorFamily:coral:1.5,colorFamily:mustard:1.5,colorFamily:terracotta:1.5,palette:earth:2,palette:warm:1.5"),
    r("SK05","Olive","skinTone",["olive"],"colorFamily:coral:2,colorFamily:rust:1.5,colorFamily:teal:1.5,colorFamily:plum:1.5,palette:earth:2,palette:warm:1.5,colorFamily:mustard:-1"),
    r("SK06","Tan","skinTone",["tan"],"colorFamily:white:1.5,colorFamily:cobalt:1.5,colorFamily:fuchsia:1.5,colorFamily:emerald:1.5,palette:bright:1.5,palette:jewel:1.5,palette:muted:-1"),
    r("SK07","Caramel","skinTone",["caramel"],"colorFamily:rust:2,colorFamily:gold:2,colorFamily:teal:1.5,colorFamily:burgundy:1.5,palette:earth:2,palette:jewel:1.5,colorFamily:beige:-1.5"),
    r("SK08","Brown","skinTone",["brown"],"colorFamily:white:2,colorFamily:red:2,colorFamily:gold:2,colorFamily:emerald:1.5,palette:bright:2,palette:jewel:2,colorFamily:beige:-1.5,palette:muted:-1.5"),
    r("SK09","Dark","skinTone",["dark"],"colorFamily:white:2.5,colorFamily:red:2,colorFamily:gold:2,colorFamily:fuchsia:1.5,colorFamily:emerald:2,palette:bright:2.5,palette:jewel:2,palette:metallic:1.5,colorFamily:beige:-1.5,palette:muted:-1.5"),
    r("SK10","Deep","skinTone",["deep"],"colorFamily:white:2.5,colorFamily:red:2.5,colorFamily:gold:2,colorFamily:fuchsia:2,colorFamily:cobalt:2,palette:bright:2.5,palette:jewel:2,colorFamily:beige:-2,palette:muted:-2"),
    r("SK11","Ebony","skinTone",["ebony"],"colorFamily:white:3,colorFamily:red:2.5,colorFamily:gold:2.5,colorFamily:fuchsia:2,colorFamily:emerald:2,palette:bright:3,palette:jewel:2.5,palette:metallic:2,colorFamily:beige:-2,palette:muted:-2"),
 
    # ══════════════════════════════════════════
    # OCCASION RULES (19)
    # ══════════════════════════════════════════
    r("OC01","Casual","occasion",["casual"],"fit:relaxed:1.5,fabric:cotton:1.5,fabric:denim:1.5,fabric:jersey:1,palette:earth:1,layering:light:1,fabric:satin:-1.5,embellishment:sequins:-2"),
    r("OC02","Office","occasion",["office"],"fit:tailored:2,fit:structured:1.5,palette:neutral:1.5,colorFamily:navy:1.5,colorFamily:charcoal:1.5,length:knee:1.5,pattern:solid:1,fit:bodycon:-2,length:mini:-2.5,pattern:animal:-2,palette:neon:-2"),
    r("OC03","Formal","occasion",["formal"],"fabric:silk:2,fabric:satin:1.5,fit:tailored:2,palette:jewel:1.5,colorFamily:black:1.5,length:maxi:1.5,embellishment:sequins:1,fabric:denim:-3,fabric:jersey:-2,fit:oversized:-2"),
    r("OC04","Wedding","occasion",["wedding"],"fabric:silk:2,fabric:chiffon:1.5,fabric:georgette:1.5,palette:jewel:1.5,length:midi:1.5,length:maxi:1,accessory:statement_jewelry:1.5,colorFamily:white:-3,colorFamily:cream:-2.5,colorFamily:ivory:-2.5,fabric:denim:-2.5"),
    r("OC05","Party","occasion",["party"],"palette:bright:2,fabric:satin:1.5,fabric:velvet:1.5,fit:bodycon:1.5,embellishment:sequins:1.5,colorFamily:black:1.5,colorFamily:red:1.5,accessory:statement_earring:1.5,fit:oversized:-1.5"),
    r("OC06","Date","occasion",["date"],"fit:tailored:1.5,fit:wrap:1.5,fabric:silk:1,colorFamily:red:1.5,colorFamily:burgundy:1,length:knee:1,accessory:delicate_jewelry:1,fit:oversized:-1.5"),
    r("OC07","Beach","occasion",["beach"],"fabric:linen:2,fabric:cotton:1.5,palette:bright:1.5,pattern:tropical:2,pattern:floral:1.5,fit:relaxed:1.5,length:maxi:1,fabric:wool:-2.5,fabric:leather:-2,layering:heavy:-2.5"),
    r("OC08","Travel","occasion",["travel"],"fabric:jersey:1.5,fabric:cotton:1.5,fit:relaxed:1.5,layering:light:1.5,palette:neutral:1,fabric:silk:-1,embellishment:sequins:-2"),
    r("OC09","Festival","occasion",["festival"],"pattern:tie_dye:2,pattern:floral:1.5,embellishment:fringe:1.5,embellishment:tassels:1.5,palette:bright:1.5,fit:relaxed:1,accessory:sunglasses:1,fit:tailored:-1.5"),
    r("OC10","Gym","occasion",["gym"],"fabric:jersey:2,fabric:mesh:1,fit:fitted:1.5,palette:dark:1,fabric:silk:-2.5,fabric:lace:-2.5,embellishment:sequins:-3"),
    r("OC11","Loungewear","occasion",["loungewear"],"fabric:cotton:2,fabric:jersey:2,fabric:fleece:1.5,fit:relaxed:2,fit:oversized:1.5,palette:pastel:1,embellishment:sequins:-2.5"),
    r("OC12","Brunch","occasion",["brunch"],"palette:pastel:1.5,pattern:floral:1.5,fabric:linen:1.5,fabric:cotton:1,fit:relaxed:1,length:midi:1,palette:neon:-1.5,embellishment:sequins:-2"),
    r("OC13","Interview","occasion",["interview"],"fit:tailored:2.5,fit:structured:2,palette:neutral:2,colorFamily:navy:2,colorFamily:charcoal:1.5,pattern:solid:1.5,length:knee:1.5,fit:bodycon:-2.5,palette:neon:-2.5,length:mini:-3"),
    r("OC14","Graduation","occasion",["graduation"],"fit:a_line:1.5,fit:tailored:1.5,palette:bright:1.5,length:knee:1.5,length:midi:1,fabric:chiffon:1,fabric:denim:-1.5,palette:neon:-1.5"),
    r("OC15","Cocktail","occasion",["cocktail"],"fabric:silk:1.5,fabric:satin:1.5,fit:tailored:1.5,length:knee:1.5,palette:jewel:1.5,colorFamily:black:1.5,fabric:denim:-2,fit:oversized:-2"),
    r("OC16","Funeral","occasion",["funeral"],"colorFamily:black:3,colorFamily:charcoal:2,colorFamily:navy:1.5,palette:dark:2.5,pattern:solid:2,length:knee:1.5,length:midi:1.5,palette:bright:-3,palette:neon:-3,colorFamily:red:-2.5,embellishment:sequins:-3"),
    r("OC17","Religious","occasion",["religious"],"fit:relaxed:1.5,fit:a_line:1.5,length:midi:2,length:maxi:2,sleeve:long:1.5,sleeve:three_quarter:1.5,palette:neutral:1,length:mini:-3,neckline:deep_v:-2.5,neckline:strapless:-2.5,fit:bodycon:-2"),
    r("OC18","Concert","occasion",["concert"],"fit:relaxed:1,palette:bright:1.5,palette:dark:1,fabric:denim:1.5,fabric:leather:1.5,accessory:sunglasses:1,fit:tailored:-1"),
    r("OC19","Hiking","occasion",["hiking"],"fabric:cotton:1.5,fabric:jersey:1.5,fabric:fleece:1,fit:relaxed:2,fit:fitted:1,layering:light:1.5,fabric:silk:-2.5,fabric:satin:-2.5,embellishment:sequins:-3"),
 
    # ══════════════════════════════════════════
    # SEASON RULES (6)
    # ══════════════════════════════════════════
    r("SN01","Spring","season",["spring"],"fabric:cotton:1.5,fabric:linen:1,palette:pastel:1.5,palette:bright:1,layering:light:1.5,sleeve:three_quarter:1,fabric:wool:-1.5,layering:heavy:-2"),
    r("SN02","Summer","season",["summer"],"fabric:linen:2,fabric:cotton:1.5,fabric:chiffon:1,sleeve:sleeveless:1.5,sleeve:short:1,palette:bright:1.5,fabric:wool:-2.5,fabric:leather:-2,fabric:velvet:-2,layering:heavy:-3"),
    r("SN03","Monsoon","season",["monsoon"],"fabric:cotton:1.5,fabric:polyester:1,palette:bright:1,palette:dark:1,length:knee:1,fabric:silk:-2,fabric:suede:-2,length:maxi:-1"),
    r("SN04","Autumn","season",["autumn"],"fabric:wool:1.5,fabric:knit:1.5,fabric:corduroy:1.5,fabric:suede:1,palette:earth:2,palette:warm:1.5,colorFamily:rust:1.5,colorFamily:burgundy:1.5,layering:medium:1.5,fabric:linen:-1,sleeve:sleeveless:-1.5"),
    r("SN05","Winter","season",["winter"],"fabric:wool:2,fabric:knit:2,fabric:velvet:1.5,fabric:tweed:1.5,fabric:fleece:1.5,fabric:leather:1,layering:heavy:2,layering:medium:1.5,palette:dark:1.5,palette:jewel:1,sleeve:long:1.5,fabric:linen:-2,fabric:chiffon:-1.5,sleeve:sleeveless:-2,layering:none:-2"),
    r("SN06","Transitional","season",["transitional"],"layering:light:2,layering:cardigan:1.5,layering:blazer:1.5,fabric:cotton:1,fabric:knit:1,sleeve:three_quarter:1.5,layering:heavy:-1.5"),
 
    # ══════════════════════════════════════════
    # STYLE PREFERENCE RULES (17)
    # ══════════════════════════════════════════
    r("ST01","Minimalist","stylePref",["minimalist"],"pattern:solid:2.5,palette:neutral:2,palette:monochrome:2,fit:tailored:1.5,colorFamily:black:1.5,colorFamily:white:1.5,embellishment:none:2,pattern:floral:-1.5,pattern:animal:-2,embellishment:sequins:-2.5,palette:neon:-2"),
    r("ST02","Boho","stylePref",["boho"],"pattern:floral:2,pattern:paisley:2,pattern:tie_dye:1.5,fabric:linen:1.5,fabric:cotton:1,fit:relaxed:1.5,embellishment:fringe:2,embellishment:tassels:1.5,accessory:bangles:1.5,palette:earth:2,fit:tailored:-1.5"),
    r("ST03","Classic","stylePref",["classic"],"fit:tailored:2,fit:structured:1.5,palette:neutral:1.5,pattern:solid:1.5,pattern:pinstripe:1,colorFamily:navy:1.5,colorFamily:charcoal:1,colorFamily:cream:1,fabric:wool:1,fabric:silk:1,palette:neon:-2.5,pattern:tie_dye:-2"),
    r("ST04","Streetwear","stylePref",["streetwear"],"fit:oversized:2,fit:boxy:1.5,pattern:geometric:1,fabric:denim:1.5,fabric:jersey:1.5,palette:dark:1,palette:neon:1,colorFamily:black:1,fit:tailored:-1.5,fabric:silk:-1.5,palette:pastel:-1.5"),
    r("ST05","Preppy","stylePref",["preppy"],"pattern:stripes:1.5,pattern:checks:1.5,pattern:plaid:1.5,fit:tailored:1.5,colorFamily:navy:1.5,colorFamily:white:1,colorFamily:pink:1,palette:pastel:1,fit:oversized:-1.5,pattern:animal:-2"),
    r("ST06","Edgy","stylePref",["edgy"],"fabric:leather:2,fabric:faux_leather:2,colorFamily:black:2.5,palette:dark:2,embellishment:studs:2,fit:slim:1.5,pattern:animal:1.5,accessory:choker:1.5,palette:pastel:-2,pattern:floral:-2"),
    r("ST07","Romantic","stylePref",["romantic"],"fabric:lace:2,fabric:chiffon:2,fabric:silk:1.5,pattern:floral:2,pattern:ditsy_floral:2,palette:pastel:2,colorFamily:blush:1.5,colorFamily:lavender:1.5,embellishment:ruffle:1.5,fit:a_line:1.5,fabric:leather:-2,palette:dark:-1.5"),
    r("ST08","Athleisure","stylePref",["athleisure"],"fabric:jersey:2,fabric:knit:1.5,fit:fitted:1.5,fit:relaxed:1,palette:neutral:1,colorFamily:black:1,colorFamily:gray:1,fabric:silk:-2,fabric:lace:-2.5,embellishment:sequins:-2.5"),
    r("ST09","Vintage","stylePref",["vintage"],"pattern:polka:1.5,pattern:floral:1.5,pattern:plaid:1,fit:a_line:1.5,waistline:high:1.5,palette:muted:1.5,embellishment:lace_trim:1,palette:neon:-2"),
    r("ST10","Cottagecore","stylePref",["cottagecore"],"pattern:ditsy_floral:2.5,pattern:floral:2,fabric:cotton:2,fabric:linen:1.5,palette:pastel:1.5,embellishment:ruffle:1.5,embellishment:lace_trim:1.5,sleeve:puff:2,fabric:leather:-2,palette:neon:-2.5"),
    r("ST11","Dark academia","stylePref",["dark_academia"],"fabric:tweed:2,fabric:wool:1.5,fabric:corduroy:1.5,palette:dark:2,palette:earth:1.5,colorFamily:brown:1.5,colorFamily:charcoal:1.5,colorFamily:burgundy:1.5,pattern:plaid:1.5,pattern:herringbone:1.5,fit:tailored:1.5,palette:neon:-2.5,pattern:tropical:-2"),
    r("ST12","Old money","stylePref",["old_money"],"fit:tailored:2.5,fabric:wool:1.5,fabric:silk:1.5,palette:neutral:2,colorFamily:navy:2,colorFamily:cream:1.5,pattern:solid:1.5,accessory:delicate_jewelry:1.5,accessory:watch:1,palette:neon:-3,pattern:animal:-2.5,embellishment:sequins:-2"),
    r("ST13","Y2K","stylePref",["y2k"],"palette:pastel:1.5,palette:bright:1.5,colorFamily:pink:1.5,fit:bodycon:1.5,fit:slim:1,length:mini:1.5,length:crop:1.5,fabric:mesh:1.5,palette:earth:-1.5"),
    r("ST14","Gothic","stylePref",["gothic"],"colorFamily:black:3,palette:dark:2.5,fabric:leather:2,fabric:velvet:2,fabric:lace:1.5,embellishment:studs:1.5,accessory:choker:2,palette:pastel:-3,palette:bright:-2,pattern:floral:-2.5"),
    r("ST15","Maximalist","stylePref",["maximalist"],"pattern:abstract:2,pattern:geometric:1.5,pattern:animal:1.5,palette:bright:2,palette:jewel:1.5,embellishment:sequins:1.5,embellishment:embroidery:1.5,accessory:statement_jewelry:2,palette:neutral:-2,pattern:solid:-2"),
    r("ST16","K-fashion","stylePref",["korean"],"fit:oversized:1.5,fit:relaxed:1,palette:pastel:1.5,palette:neutral:1,colorFamily:white:1.5,colorFamily:beige:1,fabric:cotton:1.5,pattern:solid:1,layering:light:1.5,pattern:animal:-1.5,palette:neon:-1.5"),
    r("ST17","Ethnic fusion","stylePref",["ethnic_fusion"],"embellishment:embroidery:2,embellishment:zari:1.5,embellishment:mirror_work:1.5,pattern:paisley:1.5,fabric:silk:1.5,fabric:cotton:1,palette:jewel:1.5,palette:earth:1,colorFamily:gold:1,palette:neon:-1.5"),
 
    # ══════════════════════════════════════════
    # CATEGORY RULES (14)
    # ══════════════════════════════════════════
    r("CT01","Tops","category",["tops"],"neckline:v_neck:0.5,fabric:cotton:0.5,fit:relaxed:0.5"),
    r("CT02","Bottoms","category",["bottoms"],"waistline:mid:0.5,fit:straight:0.5,fabric:denim:0.5"),
    r("CT03","Dresses","category",["dresses"],"fit:a_line:0.5,length:knee:0.5,fabric:cotton:0.5"),
    r("CT04","Outerwear","category",["outerwear"],"layering:jacket:0.5,fit:structured:0.5,fabric:wool:0.5"),
    r("CT05","Separates","category",["separates"],"fit:tailored:0.5,palette:neutral:0.5"),
    r("CT06","Accessories","category",["accessories"],"accessory:jewelry:0.5"),
    r("CT07","Footwear","category",["footwear"],"shoeStyle:sneakers:0.5,heelType:flat:0.5"),
    r("CT08","Ethnic wear","category",["ethnic"],"ethnicDetail:chikankari:0.5,embellishment:embroidery:0.5,fabric:silk:0.5"),
    r("CT09","Jumpsuits","category",["jumpsuits"],"fit:tailored:0.5,waistline:belted:0.5"),
    r("CT10","Swimwear","category",["swimwear"],"palette:bright:0.5,pattern:tropical:0.5"),
    r("CT11","Bags","category",["bags"],"bagStyle:crossbody:0.5,bagStyle:tote:0.5"),
    r("CT12","Jewelry","category",["jewelry"],"jewelryStyle:minimal:0.5,jewelryStyle:layered:0.5"),
    r("CT13","Scarves & wraps","category",["scarves_wraps"],"fabric:silk:0.5,pattern:floral:0.5"),
    r("CT14","Hats & caps","category",["hats"],"palette:neutral:0.5,colorFamily:black:0.5"),
 
    # ══════════════════════════════════════════
    # HEIGHT RULES (5)
    # ══════════════════════════════════════════
    r("HT01","Very petite","height",["very_petite"],"length:above_knee:2,length:knee:1.5,length:mini:1,fit:tailored:1.5,heelType:block:1.5,heelType:wedge:1.5,silhouette:column:1.5,palette:monochrome:1,length:maxi:-2.5,length:floor:-3,fit:oversized:-2,length:ankle:-1.5"),
    r("HT02","Petite","height",["petite"],"length:knee:2,length:above_knee:1.5,fit:tailored:1.5,heelType:block:1,silhouette:column:1.5,waistline:high:1.5,length:maxi:-2,length:floor:-2.5,fit:oversized:-1.5"),
    r("HT03","Average","height",["average"],"length:knee:1,length:midi:1,fit:tailored:0.5,fit:a_line:0.5"),
    r("HT04","Tall","height",["tall"],"length:maxi:2,length:midi:1.5,length:floor:1.5,fit:relaxed:1,fit:oversized:1,heelType:flat:1,length:crop:1,length:mini:-0.5"),
    r("HT05","Very tall","height",["very_tall"],"length:maxi:2.5,length:floor:2,length:midi:1.5,fit:relaxed:1.5,fit:oversized:1.5,heelType:flat:1.5,silhouette:layered:1.5,length:above_knee:1,fit:wrap:1"),
 
    # ══════════════════════════════════════════
    # GENDER RULES (4)
    # ══════════════════════════════════════════
    r("GN01","Men","gender",["men"],"fit:tailored:1.5,fit:straight:1.5,fit:structured:1,neckline:crew:1.5,neckline:collar:1.5,neckline:v_neck:1,fabric:denim:1,fabric:cotton:1,length:hip:1,fit:bodycon:-2.5,neckline:sweetheart:-3,neckline:halter:-3,neckline:off_shoulder:-3,neckline:strapless:-3,embellishment:ruffle:-2,embellishment:lace_trim:-2,sleeve:puff:-2,sleeve:flutter:-2"),
    r("GN02","Women","gender",["women"],"fit:a_line:1,fit:wrap:1,neckline:v_neck:0.5,neckline:scoop:0.5,neckline:sweetheart:0.5,sleeve:puff:0.5,sleeve:flutter:0.5,embellishment:ruffle:0.5,embellishment:lace_trim:0.5"),
    r("GN03","Unisex","gender",["unisex"],"fit:relaxed:1.5,fit:straight:1.5,fit:oversized:1,neckline:crew:1,fabric:cotton:1,fabric:jersey:1,palette:neutral:1,palette:dark:0.5,fit:bodycon:-1.5,neckline:sweetheart:-2,neckline:halter:-2"),
    r("GN04","Non-binary","gender",["non_binary"],"fit:relaxed:1.5,fit:oversized:1.5,fit:straight:1,neckline:crew:1,neckline:v_neck:1,palette:neutral:1,palette:monochrome:1,fabric:cotton:1,fabric:jersey:1,silhouette:column:1,fit:bodycon:-1"),
 
    # ══════════════════════════════════════════
    # AGE BRACKET RULES (6)
    # ══════════════════════════════════════════
    r("AG01","Teen","ageBracket",["teen"],"palette:bright:1.5,palette:pastel:1.5,palette:neon:1,pattern:tie_dye:1.5,pattern:geometric:1,fit:oversized:1,fit:relaxed:1,length:crop:1,length:mini:1,fabric:jersey:1,palette:dark:-0.5,fit:tailored:-0.5"),
    r("AG02","20s","ageBracket",["20s"],"palette:bright:1,fit:bodycon:1,fit:slim:1,pattern:abstract:1,pattern:geometric:0.5,length:mini:0.5,length:midi:0.5,fabric:mesh:0.5,palette:neon:0.5"),
    r("AG03","30s","ageBracket",["30s"],"fit:tailored:1.5,fit:structured:1,palette:neutral:1,palette:jewel:1,pattern:solid:1,fabric:silk:0.5,length:knee:1,length:midi:1,palette:neon:-1"),
    r("AG04","40s","ageBracket",["40s"],"fit:tailored:1.5,fit:structured:1.5,palette:neutral:1.5,palette:jewel:1,pattern:solid:1.5,fabric:silk:1,fabric:wool:0.5,length:knee:1.5,length:midi:1,palette:neon:-1.5,length:crop:-1,fit:bodycon:-1"),
    r("AG05","50s","ageBracket",["50s"],"fit:tailored:2,fit:structured:1.5,palette:neutral:1.5,palette:jewel:1.5,pattern:solid:1.5,fabric:silk:1,fabric:wool:1,length:knee:2,length:midi:1.5,palette:neon:-2,length:crop:-1.5,length:mini:-1.5,fit:bodycon:-1.5"),
    r("AG06","60s+","ageBracket",["60s_plus"],"fit:tailored:2,fit:structured:2,fit:relaxed:1.5,palette:neutral:2,palette:jewel:1.5,pattern:solid:2,fabric:silk:1,fabric:wool:1.5,fabric:knit:1.5,length:knee:2,length:midi:2,palette:neon:-2.5,length:crop:-2,length:mini:-2,fit:bodycon:-2,pattern:tie_dye:-1.5"),
 
    # ══════════════════════════════════════════
    # BUDGET TIER RULES (4)
    # ══════════════════════════════════════════
    r("BD01","Economy","budgetTier",["economy"],"fabric:cotton:1.5,fabric:jersey:1.5,fabric:polyester:1,fabric:denim:1,embellishment:none:1.5,fabric:silk:-2,fabric:leather:-2,fabric:velvet:-1.5,embellishment:sequins:-1,embellishment:beading:-1.5,embellishment:zari:-2"),
    r("BD02","Mid-range","budgetTier",["mid"],"fabric:cotton:1,fabric:linen:1,fabric:denim:1,fabric:knit:1,fabric:jersey:0.5,embellishment:embroidery:0.5,fabric:silk:-0.5,embellishment:zari:-1"),
    r("BD03","Premium","budgetTier",["premium"],"fabric:silk:1.5,fabric:wool:1.5,fabric:linen:1,fabric:leather:1,fabric:velvet:1,embellishment:embroidery:1,embellishment:sequins:0.5,fabric:polyester:-1.5,fabric:jersey:-0.5"),
    r("BD04","Luxury","budgetTier",["luxury"],"fabric:silk:2.5,fabric:wool:2,fabric:leather:2,fabric:velvet:1.5,fabric:linen:1.5,embellishment:embroidery:2,embellishment:beading:2,embellishment:sequins:1.5,embellishment:zari:2,jewelryStyle:kundan:1.5,jewelryStyle:gold:1.5,fabric:polyester:-2.5,fabric:jersey:-1.5,embellishment:none:-1"),
]
 
SEED_PRODUCTS = [
    {"name":"Floral A-Line Midi Dress","tags":["a_line","floral","midi","chiffon","v_neck","pastel"],"price":2499,"category":"dresses"},
    {"name":"Black Leather Biker Jacket","tags":["leather","black","structured","dark","studs","edgy"],"price":5999,"category":"outerwear"},
    {"name":"Silk Jewel-Tone Wrap Dress","tags":["silk","wrap","jewel","midi","tailored"],"price":3999,"category":"dresses"},
    {"name":"White Linen Beach Top","tags":["linen","white","relaxed","sleeveless","bright","cotton"],"price":1299,"category":"tops"},
    {"name":"Navy Tailored Blazer","tags":["navy","tailored","structured","neutral","wool"],"price":4499,"category":"outerwear"},
    {"name":"Red Satin Party Dress","tags":["satin","red","bodycon","bright","sequin","party"],"price":2999,"category":"dresses"},
    {"name":"Boho Paisley Maxi Skirt","tags":["paisley","maxi","earth","cotton","floral","relaxed"],"price":1799,"category":"bottoms"},
    {"name":"Gold Embroidered Ethnic Kurta","tags":["gold","embroidery","silk","jewel","ethnic","zari"],"price":3499,"category":"ethnic"},
    {"name":"Minimalist White Cotton Shirt","tags":["white","cotton","solid","neutral","tailored","monochrome"],"price":1499,"category":"tops"},
    {"name":"Velvet Emerald Evening Gown","tags":["velvet","emerald","maxi","jewel","dark","structured"],"price":6999,"category":"dresses"},
    {"name":"Knit Wool Turtleneck","tags":["knit","wool","turtle","dark","warm","heavy"],"price":1999,"category":"tops"},
    {"name":"Chiffon Ruffle Blouse","tags":["chiffon","ruffle","pastel","romantic","flutter","blush"],"price":1699,"category":"tops"},
    {"name":"Denim Straight-Leg Jeans","tags":["denim","straight","casual","cotton","mid"],"price":1999,"category":"bottoms"},
    {"name":"Lace V-Neck Wedding Guest Dress","tags":["lace","v_neck","midi","jewel","silk","chiffon"],"price":4999,"category":"dresses"},
    {"name":"Oversized Graphic Hoodie","tags":["oversized","jersey","dark","neon","boxy","streetwear"],"price":1299,"category":"tops"},
]
 