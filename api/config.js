// ប្រើ proxy របស់ Vercel (vercel.json rewrites) ដូច្នេះ browser ហៅ path តែមួយ ជាមួយ domain តែមួយ
module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).send('window.API_BASE = "";');
};
