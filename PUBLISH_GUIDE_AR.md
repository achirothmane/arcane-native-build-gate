# نشر الحزمة

تم ربط هذا المستودع بإعداد GitHub Actions. التشغيل يبدأ مع أول commit يحتوي المسارات \`.github/workflows/\` أو \`scripts/\` أو \`tests/\`.

راجع [Actions](https://github.com/achirothmane/arcane-native-build-gate/actions). إن لم تبدأ المهمة، يمكن تشغيلها يدويًا من القائمة Actions > Arcane Native Build Gate > Run workflow.

السجلات المطلوبة: \`pnpm-install.log\`، \`baseline-check.log\`، \`baseline-build.log\`، \`candidate-check.log\`، \`candidate-build.log\`، \`patch-against-original.diff\`، و\`verdict.txt\`.

لا تستنتج من نجاح البناء أن العطل المرئي اختفى. ولا تضف أسرارًا لخدمة CI.
