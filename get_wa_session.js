
function getResultFromRequest(request) {
    return new Promise((resolve, reject) => {
        request.onsuccess = function (event) {
            resolve(request.result);
        };
    });
}
  
async function getDB() {
    var request = window.indexedDB.open("wawc");
    return await getResultFromRequest(request);
}
  
async function readAllKeyValuePairs() {
    var db = await getDB();
    var objectStore = db.transaction("user").objectStore("user");
    var request = objectStore.getAll();
       return await getResultFromRequest(request);
}
  
session = await readAllKeyValuePairs();

data = JSON.stringify(session);

a = document.createElement('a');
blob = new Blob([JSON.stringify(data)], {
    type: 'text/plain'
   });
a.href = URL.createObjectURL(blob);
a.download = 'session.wa';                     //filename to download
a.click();