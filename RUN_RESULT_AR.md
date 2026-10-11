# نتيجة اختبار البناء الأصلي — 11 أكتوبر 2026

## الملخص

**نجاح 3 من 3 في فحص Svelte وبناء الواجهة الأصلية والمعدلة.**

[التشغيل الثاني الناجح على GitHub Actions](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179315515)

| إصدار Arcane | البلاغ الأصلي | فحص وبناء النسخة الأصلية | فحص وبناء النسخة المعدلة |
|---|---|---|---|
| v2.10.2 | getarcaneapp/arcane#3899 | PASS (check=0, build=0) | PASS (check=0, build=0) |
| v2.12.0 | getarcaneapp/arcane#4100 | PASS (check=0, build=0) | PASS (check=0, build=0) |
| v2.14.0 | getarcaneapp/arcane#4285 | PASS (check=0, build=0) | PASS (check=0, build=0) |

راجعت سجلات الوظائف الثلاث وملفات الأدلة التي صدرت من GitHub Actions. النتيجة في كل ملف verdict.txt هي BUILD_PASS_ONLY_RUNTIME_NOT_TESTED.

## أدلة GitHub

- [Artifact v2.10.2](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179315515/artifacts/11716948639): تعديل ملفين في واجهة التنقل.
- [Artifact v2.12.0](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179315515/artifacts/11717312670): تعديل تخطيط الترويسة.
- [Artifact v2.14.0](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179315515/artifacts/11716993548): تعديل تنسيق زر نسخ الدور.

كل حزمة أدلة تحتوي على baseline-check.log وbaseline-build.log وcandidate-check.log وcandidate-build.log وpatch-manifest.json وpatch-against-original.diff وverdict.txt، إضافةً إلى السجلات المساعدة.

## الجولة الأولى والتصحيح

[الجولة الأولى](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179110346) نجح فيها v2.10.2، بينما فشل فحص النسخة الأصلية للإصدارين الآخرين لأن ملفات Paraglide المولّدة لم تنشأ قبل Svelte check. هذا خطأ في تجهيز الاختبار وليس دليلًا على فشل الإصلاح.

عُدّل التحضير في [Commit 45e3b867](https://github.com/achirothmane/arcane-native-build-gate/commit/45e3b867449c505eaae54cc7ab0a5037bbcb7c5a)، فأصبحت الإصدارات الثلاثة تجتاز البناء الأصلي والمعدل.

## حدود النتيجة

- نجاح البناء **لا يثبت** زوال القص أو التداخل داخل Arcane أثناء التشغيل.
- التعديلات حتمية صيغت بعد دراسة البلاغات، وليست إصلاحات يولدها نموذج AI عام دون معرفة سابقة.
- لم يُشغّل backend ولم يُنجز اختبار بصري داخل Arcane بكامل مكوناته.
- لا يوجد إثبات طلب تجاري أو تفوق على أدوات المنافسين.

**القرار: TEST ONLY / NO RELEASE.** الخطوة الحاسمة هي تشغيل Arcane مع واجهة فعلية والتحقق من سلوك العطل قبل وبعد التعديل، ثم اختبار عطل مستقل لم تُصمم له القواعد.
