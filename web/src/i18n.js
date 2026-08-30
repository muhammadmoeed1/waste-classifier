import { state } from './state.js';

export const translations = {
  en: {
    tagline: 'Upload a photo to identify its waste category, then ask the AI assistant<br>anything about how to recycle it.',
    tabUpload: 'Upload Photo',
    tabCamera: 'Live Camera',
    tabMulti: 'Multi-Item',
    dropTitle: 'Drop an image here',
    dropSub: 'or click to browse &mdash; JPG, PNG, WEBP',
    classifyBtn: 'Classify waste',
    clearBtn: 'Clear',
    confidence: 'Confidence',
    gradcamLabel: 'Where the model looked (Grad-CAM)',
    gradcamHint: 'Warmer colors (red/yellow) show the regions the AI focused on most to make this prediction.',
    impactLabel: 'Environmental impact',
    feedbackPrompt: 'Wrong? Tap the right category',
    feedbackThanks: 'Thanks — feedback recorded.',
    cameraOff: 'Camera is off',
    cameraStart: 'Start camera',
    cameraStop: 'Stop',
    cameraHint: 'Classifies automatically about every 2 seconds while the camera is on (heatmap/impact are skipped here for speed &mdash; use Upload Photo for the full analysis).',
    multiDropTitle: 'Drop a photo with multiple items',
    multiDropSub: 'e.g. several items laid out on a table &mdash; JPG, PNG, WEBP',
    detectBtn: 'Detect items',
    catsLabel: 'Detectable categories',
    cat_cardboard: 'Cardboard',
    cat_glass: 'Glass',
    cat_metal: 'Metal',
    cat_paper: 'Paper',
    cat_plastic: 'Plastic',
    cat_trash: 'Trash',
    chatTitle: 'Recycling Assistant',
    chatSub: 'Powered by Groq &middot; ask about recycling rules, contamination, or your uploaded item',
    chatWelcome: 'Hi! Upload an image or just ask me a recycling question &mdash; e.g. "Can I recycle a greasy pizza box?"',
    chatPlaceholder: 'Ask about recycling...',
    suggestion1: 'Can I recycle a greasy pizza box?',
    suggestion2: "What items can't be recycled at all?",
    suggestion3: 'How should I prep items before recycling?',
    agentModeLabel: '🤖 Agent',
    toolNames: {
      lookup_recycling_guide: 'looked up recycling guide',
      estimate_environmental_impact: 'calculated CO2 impact',
      check_recyclability: 'checked recyclability',
      estimate_resale_value: 'estimated scrap resale value',
    },
    recyclable: 'Recyclable',
    notRecyclable: 'Not recyclable',
    noItemsDetected: 'No distinct items detected — try a photo with more contrast between items and background.',
    uncertainPrefix: 'Not fully sure — this might also be',
    uncertainSuffix: '. Try a clearer or closer photo for a more confident result.',
    uncertainTag: '(uncertain)',
    oodWarningText: "This doesn't look like any of the six known categories. The label below is the model's best guess, but treat it with caution.",
    classifiedMsg: (label, conf) =>
      `I classified this as **${label}** (${conf}% confidence). Ask me anything about how to recycle it!`,
    oodClarifyMsg:
      "This doesn't clearly match any of the six categories I know (cardboard, glass, metal, paper, plastic, trash). Can you describe it — what is it, and what's it made of?",
    ambiguousClarifyMsg: (label, runnerUp) =>
      `I'm genuinely torn between **${label}** and **${runnerUp}** for this one. Can you tell me more about it — what it feels like, or what it's made of?`,
  },
  ur: {
    tagline: 'تصویر اپ لوڈ کریں تاکہ اس کی کچرے کی قسم معلوم ہو، پھر AI اسسٹنٹ سے<br>ری سائیکلنگ کے بارے میں کچھ بھی پوچھیں۔',
    tabUpload: 'تصویر اپ لوڈ کریں',
    tabCamera: 'لائیو کیمرہ',
    tabMulti: 'متعدد اشیاء',
    dropTitle: 'یہاں تصویر ڈراپ کریں',
    dropSub: 'یا منتخب کرنے کے لیے کلک کریں — JPG, PNG, WEBP',
    classifyBtn: 'کچرے کی شناخت کریں',
    clearBtn: 'صاف کریں',
    confidence: 'اعتماد',
    gradcamLabel: 'ماڈل نے کہاں دیکھا (Grad-CAM)',
    gradcamHint: 'زیادہ گرم رنگ (سرخ/پیلا) ان حصوں کو ظاہر کرتے ہیں جن پر AI نے سب سے زیادہ توجہ دی۔',
    impactLabel: 'ماحولیاتی اثر',
    feedbackPrompt: 'غلط ہے؟ درست قسم پر ٹیپ کریں',
    feedbackThanks: 'شکریہ — رائے محفوظ کر لی گئی۔',
    cameraOff: 'کیمرہ بند ہے',
    cameraStart: 'کیمرہ شروع کریں',
    cameraStop: 'روکیں',
    cameraHint: 'کیمرہ آن ہونے پر ہر تقریباً 2 سیکنڈ بعد خودکار شناخت ہوتی ہے (رفتار کے لیے ہیٹ میپ/اثر یہاں شامل نہیں — مکمل تجزیے کے لیے "تصویر اپ لوڈ کریں" استعمال کریں)۔',
    multiDropTitle: 'متعدد اشیاء والی تصویر ڈراپ کریں',
    multiDropSub: 'مثلاً میز پر رکھی گئی کئی اشیاء — JPG, PNG, WEBP',
    detectBtn: 'اشیاء کی شناخت کریں',
    catsLabel: 'قابلِ شناخت اقسام',
    cat_cardboard: 'کارڈ بورڈ',
    cat_glass: 'شیشہ',
    cat_metal: 'دھات',
    cat_paper: 'کاغذ',
    cat_plastic: 'پلاسٹک',
    cat_trash: 'کچرا',
    chatTitle: 'ری سائیکلنگ اسسٹنٹ',
    chatSub: 'Groq کی طاقت سے · ری سائیکلنگ کے اصولوں، آلودگی، یا اپ لوڈ کردہ چیز کے بارے میں پوچھیں',
    chatWelcome: 'السلام علیکم! تصویر اپ لوڈ کریں یا مجھ سے کوئی سوال پوچھیں — مثلاً "کیا میں تیل والا پیزا باکس ری سائیکل کر سکتا ہوں؟"',
    chatPlaceholder: 'ری سائیکلنگ کے بارے میں پوچھیں...',
    suggestion1: 'کیا میں تیل والا پیزا باکس ری سائیکل کر سکتا ہوں؟',
    suggestion2: 'کون سی چیزیں بالکل ری سائیکل نہیں ہو سکتیں؟',
    suggestion3: 'ری سائیکلنگ سے پہلے اشیاء کو کیسے تیار کروں؟',
    agentModeLabel: '🤖 ایجنٹ',
    toolNames: {
      lookup_recycling_guide: 'ری سائیکلنگ گائیڈ دیکھی',
      estimate_environmental_impact: 'CO2 اثر شمار کیا',
      check_recyclability: 'ری سائیکل ایبلٹی چیک کی',
      estimate_resale_value: 'کباڑی کی قیمت کا اندازہ لگایا',
    },
    recyclable: 'قابلِ ری سائیکل',
    notRecyclable: 'ناقابلِ ری سائیکل',
    noItemsDetected: 'کوئی الگ چیز نہیں ملی — پس منظر اور اشیاء کے درمیان زیادہ فرق والی تصویر آزمائیں۔',
    uncertainPrefix: 'پورا یقین نہیں — یہ',
    uncertainSuffix: 'بھی ہو سکتا ہے۔ زیادہ واضح یا قریبی تصویر آزمائیں۔',
    uncertainTag: '(غیر یقینی)',
    oodWarningText: 'یہ چھ معلوم اقسام میں سے کسی سے مماثل نہیں لگتی۔ نیچے دیا گیا لیبل ماڈل کا بہترین اندازہ ہے، لیکن احتیاط سے لیں۔',
    classifiedMsg: (label, conf) =>
      `میں نے اسے **${label}** کے طور پر شناخت کیا (${conf}% اعتماد)۔ اسے ری سائیکل کرنے کے بارے میں کچھ بھی پوچھیں!`,
    oodClarifyMsg:
      'یہ میری معلوم چھ اقسام (کارڈ بورڈ، شیشہ، دھات، کاغذ، پلاسٹک، کچرا) میں سے کسی سے واضح طور پر مماثل نہیں۔ کیا آپ بتا سکتے ہیں یہ کیا ہے اور کس چیز سے بنی ہے؟',
    ambiguousClarifyMsg: (label, runnerUp) =>
      `مجھے **${label}** اور **${runnerUp}** کے درمیان واقعی تذبذب ہے۔ کیا آپ اس کے بارے میں مزید بتا سکتے ہیں — یہ چھونے میں کیسی لگتی ہے یا کس چیز سے بنی ہے؟`,
  },
};

export function t(key) {
  return (translations[state.currentLang] && translations[state.currentLang][key]) || translations.en[key] || key;
}

export function catLabel(key) {
  return t('cat_' + key);
}

export function applyLanguage(lang) {
  state.currentLang = lang;
  localStorage.setItem('lang', lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'ur' ? 'rtl' : 'ltr';
  document.body.classList.toggle('lang-ur', lang === 'ur');

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.innerHTML = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  const langToggle = document.getElementById('langToggle');
  if (langToggle) langToggle.textContent = lang === 'en' ? 'اردو' : 'English';
}

export function initI18n() {
  document.getElementById('langToggle').addEventListener('click', () => {
    applyLanguage(state.currentLang === 'en' ? 'ur' : 'en');
  });
  applyLanguage(state.currentLang);
}
