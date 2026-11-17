// Vercel Serverless Function: ส่ง backend URL จาก Environment Variable ទៅ browser
// ตั้งค่า Vercel → Project → Settings → Environment Variables:
//   AUTOSUM_API_BASE_URL = https://YOUR-BACKEND-DOMAIN   (គ្មាន /api ខាងចុង)
module.exports = (req, res) => {
  const base = (process.env.AUTOSUM_API_BASE_URL || '').replace(/\/+$/, '');
  res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).send(`window.API_BASE = ${JSON.stringify(base)};`);
};
