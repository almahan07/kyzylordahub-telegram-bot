# 🎓 Kyzylorda Hub курстарына арналған Telegram Бот (aiogram 3.x)

Бұл бот **Kyzylorda Hub** және **Astana Hub** білім беру бағдарламалары аясында пайдаланушыларға ресми курстарды таңдауға, Instagram-ға жазылу шартын орындап, курсқа арналған **арнайы промокод пен тікелей сілтемені** алуға мүмкіндік береді.

---

## 📚 Курстар мен промокодтар тізімі (Google Sheets бойынша):

| № | Курс атауы | Kyzylorda Hub промокоды | Лимит | edu.astanahub.com сілтемесі |
|---|---|---|---|---|
| 1 | 💻 **No Code / Low Code School** | `KYZYLORDA-HUB-NLC` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/8d83f744-1846-43ea-bc2a-1b8a37084a2e) |
| 2 | 🚀 **Startup Academy** | `KYZYLORDA-HUB-SA` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/cc946059-304e-450a-895b-e671db651cba) |
| 3 | 🎓 **Startup School** | `KYZYLORDA-HUB-SS` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/f2159fbf-0ecf-43cb-9376-b7efc6fc7df5) |
| 4 | 💼 **Freelance School** | `KYZYLORDA-HUB-FS` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/3dcbfff1-1a89-4c9b-a2c3-c58c0425ac6d) |
| 5 | 🤖 **Prompt Engineering** | `KYZYLORDA-HUB-PE` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/74b6914d-7e3b-4f52-b0ae-8f989e2294a7) |
| 6 | 📈 **Beta Career** | `KYZYLORDA-HUB-BC` | 100 | [Курсқа өту](https://edu.astanahub.com/courses/c9d1629b-f2c2-40b8-9097-c92623ced30d) |

---

## 📋 Боттың негізгі мүмкіндіктері

1. **Курс таңдау:**
   - 6 ресми курс бойынша ыңғайлы Inline-мәзір.
2. **Instagram-ға тіркелу:**
   - Ресми [@kyzylordahub](https://www.instagram.com/kyzylordahub/) аккаунтына жазылу батырмасы.
3. **Промокод пен тікелей сілтеме беру:**
   - Пайдаланушыға таңдаған курсының промокоды беріледі.
   - Хабарлама астындағы **«🚀 Курсқа өту (edu.astanahub.com)»** батырмасы арқылы пайдаланушы бірден сол курстың нақты парақшасына өтіп, промокодты енгізе алады.
4. **1 қолданушы = 1 промокод ережесі:**
   - Бір пайдаланушы қайта /start басса, бұрын алған промокодын қайтарып көрсетеді.
5. **Лимит есебі (Usage Limit):**
   - Әр курс бойынша 100 промокод лимиті қадағаланады. Лимит таусылса, әкімшіге дабыл жіберіледі.
6. **Админ басқару:**
   - `/stats` — Әр курс бойынша барлығы, берілгені және қалғаны.
   - `/upload` — Қосымша жеке промокодтар файлын жүктеу.
   - `/broadcast` — Барлық пайдаланушыларға хабар тарату.

---

## 🚀 Іске қосу

```bash
# Виртуалды ортаны қосу:
.\venv\Scripts\activate

# Ботты қосу:
python main.py
```

---

## ⚡ Render.com-да 24/7 Үздіксіз жұмыс істету (Ноутбуксіз)

Render Free Web Service 15 минут сұраныс болмаса автоматты түрде ұйықтап қалады («sleep mode»). Бот 24/7 ноутбук өшіп тұрса да жұмыс істеуі үшін келесі шешімдер орнатылды:

### 1. GitHub Actions (Бұлтты автобот — 100% тегін)
- Жобада `.github/workflows/render_keep_alive.yml` орнатылған.
- `push_to_github.bat` файлын басқан бойда, GitHub Actions бұлты әр 5-10 минут сайын `https://kyzylordahub-telegram-bot-1.onrender.com/health` адресіне сұраныс жіберіп, ботты ояу ұстайды.

### 2. Боттың ішкі авто-пингері (main.py)
- Бот қосылғаннан кейін өзінің адресіне әр 5 минут сайын GET сұраныс жіберіп, Render таймерін нөлдеп отырады.

### 3. UptimeRobot немесе cron-job.org (Ең сенімді тәсіл):
1. **[cron-job.org](https://cron-job.org)** немесе **[uptimerobot.com](https://uptimerobot.com)** сайтына кіріп, тегін тіркеліңіз.
2. «Create Monitor» / «Create Cronjob» басыңыз:
   - **URL:** `https://kyzylordahub-telegram-bot-1.onrender.com/health`
   - **Интервал:** 5 минут (Every 5 minutes).
3. Сақтаңыз! Енді Render ботыңыз ноутбук өшіп тұрса да 24/7 тоқтаусыз жұмыс істейді.

