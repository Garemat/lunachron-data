/**
 * Paste this into the browser console while on https://app.moontome.com/Compendium
 * It reads every object store from the 'moonstoneModels' IndexedDB and downloads
 * the result as moonstone_db.json — feed that file to compare_db.py.
 */
(() => {
  const DB_NAME = 'MoontomeDb';

  const open = () => new Promise((res, rej) => {
    const req = indexedDB.open(DB_NAME);
    req.onsuccess = e => res(e.target.result);
    req.onerror = e => rej(e.target.error);
  });

  const dumpStore = (db, name) => new Promise((res, rej) => {
    const tx = db.transaction(name, 'readonly');
    const req = tx.objectStore(name).getAll();
    req.onsuccess = e => res({ [name]: e.target.result });
    req.onerror = e => rej(e.target.error);
  });

  open().then(async db => {
    const stores = [...db.objectStoreNames];
    const parts = await Promise.all(stores.map(n => dumpStore(db, n)));
    const combined = Object.assign({}, ...parts);
    const blob = new Blob([JSON.stringify(combined, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'moonstone_db.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    console.log('Downloaded moonstone_db.json —', stores, 'stores');
  }).catch(console.error);
})();
