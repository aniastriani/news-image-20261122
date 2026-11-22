# news-image-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/aniastriani/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/aniastriani/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

The World in One Image — Sunday 22 November 2026. A newspaper front
page that sums up the day's world news in one picture: Trump lands in
Shenzhen for the APEC summit, with a trilateral meeting with Xi and
Putin planned; Estonia will shut its border with Russia; US airlines
are warned of a possible attack plot ahead of Thanksgiving; France
turns to the UN Security Council after Myanmar rejects the world
court's genocide ruling; COP31 climate talks close in on a final deal;
and Mexico arrests "El Chapo Isidro", the FBI's most-wanted drug lord.

`main.py` draws the whole page with the Python standard library only —
a hand-built 5x7 pixel font stored as rows of five bits, small vector
pictograms, and a PNG writer built by hand. No network, no clock, no
randomness: every run writes the same bytes.

## Run it

```sh
python3 main.py
```

The picture is written to `/output/entry.png`, or to
`$MAKEFUN_OUTPUT_DIR` when that variable is set.

---

<sub>Entry for the [news-image-20261122](https://make.fun/bounty/news-image-20261122) bounty on [make.fun](https://make.fun).</sub>
