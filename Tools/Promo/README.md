# Promo 對比圖合成腳本

圖的來源：編輯器工具列 **Promo Final / Promo Grey / Promo Shot**（`Content/Python/promo_shots.py`），同機位的灰盒 / 最終畫面存在 `Saved/Promo/<關卡>_<編號>_grey.png` / `_final.png`（`Saved/` 不進 git）。

| 腳本 | 用途 |
|------|------|
| `split_soft.ps1` | 斜線柔邊過渡（左灰盒、右最終畫面）。`-Feather` 過渡帶寬（畫面寬的比例，0.18 = 寬漸變），`-Noise` > 0 變成水彩筆刷邊，`-Top` / `-Bottom` 分界線在上 / 下緣的位置 |
| `split_hard.ps1` | 斜線硬邊＋白色分界線 |
| `crop169.ps1` | 從中間裁成 16:9（全高） |
| `label.ps1` | 主選單風格標籤：橄欖綠小標籤壓在米色紙片上（EDIT MODE / PLAY MODE ＋一句說明） |
| `label2.ps1` | 16:9 裁切＋主選單 logo（`Tools/MainMenu/Assets`）＋底部小標籤 |

例（itch.io 用的 16:9 全景，見 Level1_08）：

```powershell
.\split_soft.ps1 -Grey Saved\Promo\Level1_08_grey.png -Final Saved\Promo\Level1_08_final.png -Out soft.png -Top 0.562 -Bottom 0.438 -Feather 0.14
.\crop169.ps1 -In soft.png -Out soft169.png
.\label.ps1 -In soft169.png -Out Level1_overview_16x9.png
```

itch.io 單張圖上限 3 MB：最後轉成 JPG（品質 95，約 0.5 MB）再上傳。16:9 時拍攝 FOV 要放大，裁切後左右範圍才不變：`FOV169 = 2·atan(tan(FOV/2)·視口寬/(視口高·16/9))`。