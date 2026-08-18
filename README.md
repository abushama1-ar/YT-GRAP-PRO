 
# YT-GRAP-PRO
برنامج تحميل فيديوهات من كافة مواقع الانترنت مفتوح المصدر

[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&style=for-the-badge)](https://discord.gg/GpzW8kv4pM)

---

## ⚠️ تنبيه مهم | Important Notice

### 🚫 هذا المستودع لا يتم تطويره حالياً
**الحالة:** المشروع متوقف عن التطوير

المطور قرر الانتقال من لغة **Python** إلى **C# .NET** ولن يقوم بتطوير هذا المشروع في المستقبل القريب.

### 📢 ما يمكنك فعله:
- **خذ نسخة خاصة بك:** يمكنك عمل Fork من هذا المستودع وتطويره بشكل مستقل
- **ابحث عن مشاريع أخرى:** المطور لديه مشاريع أخرى مبنية على C# WPF (مغلقة المصدر لكنها مجانية للتحميل)

---

### 🚫 This Repository is Not Currently Maintained
**Status:** Project is discontinued

The developer has decided to migrate from **Python** to **C# .NET** and will not be developing this project in the near future.

### 📢 What You Can Do:
- **Fork this repository:** You can create your own fork and continue development independently
- **Explore other projects:** The developer has other projects built with C# WPF (closed-source but free to download)

---

## ⚠️ تحذير هام جداً | ⚠️ IMPORTANT WARNING

### العربية 🇸🇦
# **تحذير هام جداً**
## **سورس الكود يتطلب مجلد `bin` بجانبه**
### يجب أن يحتوي هذا المجلد على:
- **محرك FFmpeg** وكافة التبعيات المطلوبة
- **بدون هذا المجلد لن يعمل أي فيديو**

### تثبيت FFmpeg
قم بتحميل FFmpeg من الموقع الرسمي:
🔗 **[FFmpeg الموقع الرسمي](https://ffmpeg.org/download.html)**

---

### English 🇺🇸
# **VERY IMPORTANT WARNING**
## **Source Code Requires a `bin` Folder Next to It**
### This folder must contain:
- **FFmpeg Engine** and all required dependencies
- **Without this folder, no video will work**

### Install FFmpeg
Download FFmpeg from the official website:
🔗 **[FFmpeg Official Website](https://ffmpeg.org/download.html)**

---

## حول المشروع
برنامج مفتوح المصدر يتيح تحميل الفيديوهات من مختلف مواقع الإنترنت بسهولة.

---

## مثال: تضمين PayPal JS SDK
فيما يلي مثال صفحة HTML صغيرة لدمج PayPal JS SDK. أضفت هذا المثال كما طلبت — يمكنك نسخه إلى ملف HTML مستقل (مثلاً `pay.html`) أو عرضه في README كقطعة كود.

> ملاحظة: تجنب نشر `client-id` علنًا في المستودع العام. استبدل القيمة أو استخدم متغير بيئة عند النشر.

```html
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>PayPal JS SDK Standard Integration</title>
    </head>
    <body>
        <div id="paypal-button-container"></div>
        <p id="result-message"></p>

       
        <!-- Initialize the JS-SDK -->
        <script
            src="https://www.paypal.com/sdk/js?client-id=AVOnwg0ZYES07VHFo3VTkGFBRTZBdFTAZXWL2VDUUpnJQMUVRA9Swp3KQ0tHLApHLZZEevLgm3-1Iv-h&buyer-country=US&currency=USD&components=buttons"
            data-sdk-integration-source="developer-studio"
        ></script>
        <script src="app.js"></script>
       
    </body>
</html>
```

الآن يمكنك:
- إضافة ملف `pay.html` إلى المستودع وتجربة العرض محليًا.
- إعداد GitHub Pages لعرض الملف كصفحة ثابتة إن رغبت.

إذا تريد، أستطيع:
- إنشاء ملف `pay.html` في المستودع يحتوي على المثال.
- أو إزالة `client-id` ووضع تعليمات لاستخدام متغير بيئة.
