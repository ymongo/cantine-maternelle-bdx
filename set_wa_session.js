function getResultFromRequest(request) {
	return new Promise((resolve, reject) => {
		request.onsuccess = function(event) {
			resolve(request.result);
		};
	})
}

async function getDB() {
	var request = window.indexedDB.open("wawc");
	return await getResultFromRequest(request);
}

async function injectSession(SESSION_STRING) {
    try {
        var session = JSON.parse(SESSION_STRING);
        var db = await getDB();
        // var objectStore = db.transaction("user", "readwrite").objectStore("user", { keyPath: "key", autoIncrement:true });
        var objectStore = db.createObjectStore("user", { keyPath: "key", autoIncrement:true });
        objectStore.autoIncrement = true
        console.log(session)

        console.log(objectStore)
        for(var keyValue of session) {
            var request = objectStore.put(keyValue);
            await getResultFromRequest(request);
        }
    } catch(error) {
        console.log(error)
    }


}

// var SESSION_STRING = "";
await injectSession(arguments[0]);
