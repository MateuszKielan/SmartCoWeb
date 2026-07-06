// Smart Cow Web — client behaviour.
// UI state lives in the Alpine `smartcow()` component; server interactions use
// htmx (match/vocabulary fragments) and small fetch() calls (convert/save/etc).

// ---- CSRF helpers ----------------------------------------------------------
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Attach the CSRF token to every htmx request automatically.
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});

// ---- Alpine component ------------------------------------------------------
function smartcow() {
    return {
        // UI state
        sidebarOpen: false,
        activePopup: null,      // 'requestType' | 'vocabRecommender' | 'navSearch' | 'support' | 'vocabManager'
        showDataset: false,
        showMatches: false,
        showInsert: false,
        searchHelp: false,          // help overlay for the Quick Search popup
        scoresHelp: false,          // help overlay explaining the match/vocab scores
        matchTitle: 'Matches',
        searchValue: '',
        colorBlind: false,
        toast: { show: false, message: '', type: 'success', downloadUrl: null },

        // Vocabulary manager
        vocabInput: '',
        vocabList: [],

        // Currently selected match row for the insert popup
        insert: { row: [], header: '' },

        // Match-window resizing
        _resize: { active: false, startY: 0, startHeight: 0 },

        // --- JSON / metadata editor state ---
        jsonView: 'structured',     // 'raw' | 'structured'
        jsonText: '',               // single source of truth for the metadata JSON
        meta: {},                   // parsed metadata object (structured mode)
        settingsObj: {},            // @context entry holding @base / @language
        nsObj: null,                // @context entry holding the namespaces
        namespaces: [],             // [{ prefix, uri }] editable view of nsObj
        publisher: {},              // reference to meta['dc:publisher']
        license: {},                // reference to meta['dc:license'] ({ '@id': ... })
        tableSchema: {},            // reference to meta.tableSchema
        columns: [],                // reference to meta.tableSchema.columns
        openColumns: [],            // indices of expanded column cards

        init() {
            try {
                this.colorBlind = localStorage.getItem('colorBlindMode') === '1';
            } catch (e) { /* ignore */ }
            document.documentElement.classList.toggle('color-blind', this.colorBlind);

            // Seed the editor from the server-rendered textarea.
            const el = document.getElementById('jsonPreview');
            if (el) this.jsonText = el.value;

            // Default view is the structured editor; parse now (fall back to raw
            // if the metadata isn't valid JSON).
            if (this.jsonView === 'structured' && !this.parseMeta(true)) {
                this.jsonView = 'raw';
            }
        },

        // --- generic helpers ---
        openPopup(name) { this.activePopup = name; },

        closeAll() {
            this.activePopup = null;
            this.showMatches = false;
            this.showInsert = false;
            this.showDataset = false;
            this.searchHelp = false;
            this.scoresHelp = false;
            this.sidebarOpen = false;
        },

        openLink(url) { window.open(url, '_blank'); },

        toggleColorBlind() {
            this.colorBlind = !this.colorBlind;
            document.documentElement.classList.toggle('color-blind', this.colorBlind);
            try { localStorage.setItem('colorBlindMode', this.colorBlind ? '1' : '0'); } catch (e) {}
        },

        toastMsg(message, type = 'success', downloadUrl = null) {
            this.toast = { show: true, message, type, downloadUrl };
            clearTimeout(this._toastTimer);
            this._toastTimer = setTimeout(() => { this.toast.show = false; }, downloadUrl ? 10000 : 4000);
        },

        // --- match / vocabulary loading (htmx) ---
        loadMatches(header) {
            if (!header) return;
            this.matchTitle = header;
            this.showMatches = true;
            htmx.ajax('GET', `/matches/?header=${encodeURIComponent(header)}`,
                      { target: '#match-content', swap: 'innerHTML' });
        },

        loadVocabRanking() {
            this.matchTitle = 'Vocabulary ranking';
            this.showMatches = true;
            htmx.ajax('GET', '/vocab_ranking/',
                      { target: '#match-content', swap: 'innerHTML' });
        },

        // --- insert flow ---
        openInsert(dataset) {
            this.insert = { row: JSON.parse(dataset.row), header: dataset.header };
            this.showInsert = true;
        },

        openSource() {
            const uri = this.insert.row[2];
            if (uri) window.open(uri, '_blank');
        },

        doInsert() {
            fetch('/insert_match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ row: this.insert.row, header: this.insert.header }),
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.status === 'success') {
                        this.jsonText = data.json;
                        if (this.jsonView === 'structured') this.parseMeta();
                        this.toastMsg(`Inserted match for "${this.insert.header}".`);
                    } else {
                        this.toastMsg(data.message || 'Failed to insert match.', 'error');
                    }
                    this.showInsert = false;
                })
                .catch(() => this.toastMsg('Failed to insert match.', 'error'));
        },

        // --- conversion / save ---
        convert() {
            this.toastMsg('Converting to N-Quads…', 'success');
            fetch('/convert/nquads/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.status === 'success') {
                        this.toastMsg(data.message, 'success', data.download_url);
                    } else {
                        this.toastMsg(data.message || 'Conversion failed.', 'error');
                    }
                })
                .catch(() => this.toastMsg('An error occurred during conversion.', 'error'));
        },

        saveFile() {
            // In structured mode, serialise the editor back into jsonText first.
            if (this.jsonView === 'structured' && !this.buildJson()) return;

            const formData = new FormData();
            formData.append('json_text', this.jsonText);
            fetch('/save_file', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                body: formData,
            })
                .then((r) => r.json())
                .then((data) => this.toastMsg(data.message, data.status === 'success' ? 'success' : 'error'))
                .catch(() => this.toastMsg('Failed to save the file.', 'error'));
        },

        // --- metadata editor (structured view) ---
        setJsonView(view) {
            if (view === this.jsonView) return;
            if (view === 'structured') {
                if (!this.parseMeta()) return;   // stay on raw if JSON is invalid
            } else {
                this.buildJson();                // sync edits back into the textarea
            }
            this.jsonView = view;
        },

        parseMeta(silent = false) {
            try {
                this.meta = JSON.parse(this.jsonText);
            } catch (e) {
                if (!silent) this.toastMsg('Cannot open editor: the JSON is invalid.', 'error');
                return false;
            }

            // Normalise @context into an array we can edit.
            let ctx = this.meta['@context'];
            if (!Array.isArray(ctx)) ctx = ctx ? [ctx] : [];
            this.meta['@context'] = ctx;

            // The entry carrying @base / @language.
            this.settingsObj = ctx.find(
                (e) => e && typeof e === 'object' && ('@base' in e || '@language' in e)
            );
            if (!this.settingsObj) {
                this.settingsObj = { '@base': '', '@language': '' };
                ctx.push(this.settingsObj);
            }

            // The entry holding the prefix -> URI namespaces.
            this.nsObj = ctx.find(
                (e) => e && typeof e === 'object' && e !== this.settingsObj &&
                       Object.keys(e).some((k) => !k.startsWith('@'))
            );
            this.namespaces = this.nsObj
                ? Object.entries(this.nsObj).map(([prefix, uri]) => ({ prefix, uri }))
                : [];

            // Dataset descriptors. Ensure the parent objects exist so the editor
            // can bind to their sub-keys.
            const pub = this.meta['dc:publisher'];
            this.publisher = (pub && typeof pub === 'object')
                ? pub
                : (this.meta['dc:publisher'] = { 'schema:name': typeof pub === 'string' ? pub : '' });
            const lic = this.meta['dc:license'];
            this.license = (lic && typeof lic === 'object')
                ? lic
                : (this.meta['dc:license'] = { '@id': typeof lic === 'string' ? lic : '' });

            // References into meta (edits flow straight through).
            this.tableSchema = this.meta.tableSchema || (this.meta.tableSchema = {});
            this.columns = this.tableSchema.columns || (this.tableSchema.columns = []);
            this.openColumns = [];
            return true;
        },

        buildJson() {
            try {
                // Rebuild the namespaces object in place from the editable list.
                if (this.nsObj) {
                    Object.keys(this.nsObj).forEach((k) => delete this.nsObj[k]);
                    this.namespaces.forEach(({ prefix, uri }) => {
                        if (prefix) this.nsObj[prefix] = uri;
                    });
                } else if (this.namespaces.length) {
                    const obj = {};
                    this.namespaces.forEach(({ prefix, uri }) => { if (prefix) obj[prefix] = uri; });
                    this.meta['@context'].push(obj);
                    this.nsObj = obj;
                }
                this.jsonText = JSON.stringify(this.meta, null, 4);
                return true;
            } catch (e) {
                this.toastMsg('Could not serialise the metadata.', 'error');
                return false;
            }
        },

        addNamespace() { this.namespaces.push({ prefix: '', uri: '' }); },
        removeNamespace(i) { this.namespaces.splice(i, 1); },

        toggleColumn(i) {
            const at = this.openColumns.indexOf(i);
            if (at === -1) this.openColumns.push(i);
            else this.openColumns.splice(at, 1);
        },
        isColumnOpen(i) { return this.openColumns.includes(i); },

        // --- support form ---
        submitSupport(event) {
            const formData = new FormData(event.target);
            fetch('/submit-support/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                body: formData,
            })
                .then((r) => r.json())
                .then((data) => {
                    this.toastMsg(data.message, data.status === 'success' ? 'success' : 'error');
                    if (data.status === 'success') {
                        event.target.reset();
                        this.activePopup = null;
                    }
                })
                .catch(() => this.toastMsg('Failed to submit the request.', 'error'));
        },

        // --- vocabulary manager ---
        addVocabulary() {
            const name = this.vocabInput.trim();
            if (!name || this.vocabList.includes(name)) { this.vocabInput = ''; return; }
            this.vocabList.push(name);
            this.vocabInput = '';
        },

        removeVocabulary(idx) { this.vocabList.splice(idx, 1); },

        moveVocabulary(idx, dir) {
            const target = idx + dir;
            if (target < 0 || target >= this.vocabList.length) return;
            [this.vocabList[idx], this.vocabList[target]] = [this.vocabList[target], this.vocabList[idx]];
        },

        submitPriorityList() {
            fetch('/vocabulary_manager/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ priority_list: this.vocabList }),
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.status === 'success') {
                        this.jsonText = data.json;
                        if (this.jsonView === 'structured') this.parseMeta();
                        this.toastMsg('Priority applied to the recommendations.');
                        this.activePopup = null;
                    } else {
                        this.toastMsg(data.message || 'Failed to apply the priority list.', 'error');
                    }
                })
                .catch(() => this.toastMsg('Failed to submit the priority list.', 'error'));
        },

        // --- resizable match window ---
        startResize(event) {
            this._resize = {
                active: true,
                startY: event.clientY,
                startHeight: this.$refs.matchContainer.offsetHeight,
            };
            const onMove = (e) => {
                if (!this._resize.active) return;
                const dy = this._resize.startY - e.clientY;
                this.$refs.matchContainer.style.height = `${this._resize.startHeight + dy}px`;
            };
            const onUp = () => {
                this._resize.active = false;
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
            };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        },
    };
}
