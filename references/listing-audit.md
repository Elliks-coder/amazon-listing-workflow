# C · Listing Audit

## 站点规则

先核对目标站点 Seller Central 的当前规则、适用日期和例外，再核对指定商品类型的最新 Product Type Definitions 与 A+ 模板约束（适用时）。记录站点、语言、商品类型、具体字段上限、计量单位、来源和核对日。审核发现政策与 API 表单检查不同的计量口径时，同时验证两个适用条件。缺少受限字段的官方说明时，按有明确依据的部分继续并标为待核实。

### 加拿大站参考

以下来源于 2026-11-24 核对。使用时重新确认适用范围与当前要求。

- **标题**。普通非媒体类目自 2026-07-27 起最多 **75 字符（含空格）**。标题通常同一个词最多两次，介词、冠词和连词有例外，具体重复语境及专名需复核。检查促销文字和禁用符号 `! $ ? _ { } ^ ¬ ¦`，以及仅可在特定语境使用的装饰符号。媒体类目按具体规则。Amazon 公告同时列了 Egypt、Saudi Arabia、Türkiye、United Arab Emirates 的站点例外，其他站点核对当地规则。[加拿大标题规则](https://sellercentral.amazon.ca/help/hub/reference/external/GYTR6SYGFA5E3EQC) · [生效日期和例外](https://sellercentral.amazon.ca/help/hub/reference/external/GQHQGBTD7XB7EECN)
- **Item Highlights**。适用类目最多 **125 字符（含空格）**，按逗号分隔的短语写。核对 Seller Central 或目标类目中字段是否可用。通过 API 预检时用实际返回的字段定义与支持情况。[加拿大标题及 Highlights 规则](https://sellercentral.amazon.ca/help/hub/reference/external/GYTR6SYGFA5E3EQC)
- **五点描述、长描述和 A+**。实际 bullet、长描述和 A+ 的上限、条数及格式按商品类型和模块核定。按类目要求审核字符，五点低于写作参考长度时可以通过。检查宣传表述、促销/退款承诺、站外链接、联系资料、引述买家评价、医疗与认证声明等内容，按对应字段和当地政策判定。[五点要求](https://sellercentral.amazon.ca/help/hub/reference/external/GX5L8BF8GLMML6CX) · [详情页规则](https://sellercentral.amazon.ca/help/hub/reference/external/G200390640) · [A+ 准则](https://sellercentral.amazon.ca/help/hub/reference/external/GGW8U76SSNTRTBX7) · [类目字段 API](https://developer-docs.amazon/sp-api/docs/product-type-definitions-api)
- **Search Terms**。加拿大帮助页要求 **少于 250 字节**，并说明 Amazon 搜索计长时忽略空格和标点。保留实际 UTF-8 字节数和按该帮助页口径的去空白、去标点字节数。若目标字段或所用渠道另有原始 UTF-8 上限，也据其检查，Seller Central 录入器和 SP-API 预检分别记录结果。[加拿大 Search Terms 帮助](https://sellercentral.amazon.ca/gp/help/external/G23501)

## 确定性检查

在最终文案上运行 [audit_listing.py](../scripts/audit_listing.py)，将 UTF-8 JSON 文件作为参数传入，可用 `python -X utf8 <脚本路径> <草稿 JSON 路径>`。也支持 JSON 标准输入。绝对路径用引号。仅输入文案和已核验的规则参数。根据业务站点填写 `limits`，下面是加拿大普通非媒体类目的精简输入说明：

```json
{
  "fields": {
    "title": "Brand Metal Floor Lamp, Black",
    "item_highlights": "Foot switch, slim profile",
    "bullet_points": ["Turn the lamp on and off with the foot switch"],
    "description": "Draft description",
    "search_terms": "standing reading light",
    "aplus": {"hero": {"headline": "Light for a Reading Corner"}}
  },
  "limits": {
    "title": {"characters": 75},
    "item_highlights": {"characters": 125},
    "search_terms": {"non_separator_utf8_bytes": 249}
  },
  "search_terms_exclude_frontend": true,
  "title_repetition": {
    "max_occurrences": 2,
    "ignore_words": ["a", "an", "the", "to", "in", "of", "for", "with", "and", "or"]
  },
  "blocked_terms": {
    "title": ["free shipping"],
    "search_terms": ["example competitor brand"]
  },
  "blocked_characters": {
    "title": "!$?_{}^¬¦"
  }
}
```

`limits` 支持 `characters`、`utf8_bytes` 和 `non_separator_utf8_bytes`。所有配置值表示允许的最大值。`bullet_points` 作为配置键时应用到每一条，`bullet_points[1]` 可补充该条的新计量项或覆盖同名上限（从 1 开始）。嵌套 A+ 字段用点路径。`blocked_terms` 匹配词或词组，`blocked_characters` 匹配原文中的单个禁用字符，两者均按字段配置。字符按 Unicode 码点计，原始字节用 UTF-8 编码。去分隔符的结果按当前加拿大帮助页执行，具体界面计数有出入时用官方录入器核对。对连字符、语言中的复合词和无空格语言，同时做人工语义核对。完整流程传入 `search_terms_exclude_frontend: true`，用脚本查后台词是否已出现在标题、Item Highlights、五点和长描述，并报告出现的字段。单复数、间隔和拼写变体造成的冗余要结合语境再核对。

## 证据与合规检查

1. 对照 A 的卖点证据表逐字段核对功能、配件、尺寸、材料、兼容性、适用场景、年龄、保修期、认证、检测结果和任何可量化承诺。发现冲突或缺证时，以现有证据改写或移到待确认项。
2. 检查标题、Highlights、五点、长描述与 A+ 是否在回答不同的选购问题。判断词的相关性、跨字段机械重复、近义重复和违和的搜索意图。对后台词复核四个前台字段的词、品牌/ASIN、重复词、适配证据和总字节。把实际使用位置和筛词原因与交付词库核对。正常重复出现的品类名或信息可保留，具体词频限制遵循字段规则。
3. 对照站点政策、品类要求和原始资料检查未经支持的性能、绝对化/疗效/认证宣传、促销、竞品商标、评论引述、URL、联系资料和其他字段禁用内容。变体家庭的共用声明要逐款适用。
4. 修复可以直接修复的问题并运行脚本复检。用户明确要亚马逊预检且已具备必要资料时，可用 `VALIDATION_PREVIEW` 核对 API 字段及报错。[亚马逊预检说明](https://developer-docs.amazon/sp-api/docs/preview-errors-before-creating-a-listing)

## 转化信息密度

1. 核对每条是否增加了规格、操作信息或具体用法。场景句能解释买家何时会用、能省什么事就保留。合并重复事实，删掉泛化氛围句和通用装修建议。按 [体验说明](listing-writer.md#何时把规格翻成使用体验) 核对时间换算的条件、光色对应的依据和最相关的操作疑问。其余小缺项交用户复核。
2. 对照调研排序检查第一条。对无线或电池灯，先核对钻孔、适用表面、五金件和所选场景与实际安装方式一致。最强视觉差异排第一时，紧接交代安装信息。检查其余条目分别回答充电、灯效、规格或场景等不同问题。
3. 在标题和 Item Highlights 逐项查 [Top 3](listing-research.md#写前锁定-top-3-与字段落位)，记录实际词组及字段。优先由标题或 Highlights 补齐遗漏。仍无法落位时，在简报中用 `🔴 未覆盖` 标出缺项与原因。所有证据待补项只保留在内部审稿字段。

## 主图基础排查

仅对用户提供、指定或明确要用作主图的图片进行检查。按目标站和商品类型核对清晰度、像素尺寸、背景、主体占比与裁切，并核对是否有叠加文案、水印和额外道具。查颜色、款式、套装数量、配件是否与当前 SKU 和文案一致。加拿大站按官方主图指南核对纯白背景、约 85% 的主体构图，以及多件装规则和适用例外。交付「可用 / 需整改 / 待提供原图」和具体问题，低清截图只供预览核对。 [加拿大站商品图片指南](https://sellercentral.amazon.ca/help/hub/reference/external/G1881?lang=en-gb)

## 商品字段与提交准备

当交付包含上架字段时，按商品类型、变体、现有 ASIN 或新品、配送方式核对结构化必填项。品牌、标识符、规格和相应证据缺失时，说明受影响的字段和 SKU。把商品字段是否齐全和文案是否通过分列记录。资料不足时交付已证实的文案草稿，标明“待补商品资料”。

## 审核交付

输出字段检查表（字段｜实测字符/字节｜适用上限｜问题｜修改或待确认项），并附已修好的干净版本。区分会阻止提交的字段缺失或违规、需要用户举证的声明和可改善项。附 Top 3 落位、五点精简结果与主图检查状态。交付网页报告时验证按类型筛选和文字搜索可同时使用。给出尚需确认的关键资料和已核对的来源。数据或预检尚待核验时，使用“待确认”或“文案审核通过，待平台预检”等状态。
