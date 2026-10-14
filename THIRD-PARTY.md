# Fremdcode und Lizenzen / Third-Party Notices

PyPad steht unter der **MIT-Lizenz** (siehe [LICENSE](LICENSE)). Das Programm enthält
**Fremdcode** von Dritten, der unter einer eigenen Lizenz steht. Die folgenden Hinweise sind
Bestandteil dieser Lizenz und müssen beim Weitergeben (Quelltext oder Binärform) mitgeliefert
werden.

## 1. Ace — Editor-Komponente (mitgeliefert)

- **Paket:** ace-builds, **Version 1.44.0**
- **Quelle:** https://github.com/ajaxorg/ace · veröffentlicht als https://www.npmjs.com/package/ace-builds
- **Lizenz:** BSD 3-Clause License („New"/„Revised" BSD)
- **Rechteinhaber:** Copyright (c) 2010, Ajax.org B.V. — All rights reserved.
- **Mitgelieferte Dateien** (unverändert übernommen, Ordner `vendor/`):

| Datei | Zweck | SHA-256 (stimmt mit ace-builds@1.44.0 überein) |
|---|---|---|
| `ace.js` | Editor-Kern | (siehe Prüfsummen unten) |
| `mode-python.js` | Python-Syntaxhervorhebung | |
| `theme-tomorrow_night.js` | Farbschema | |
| `ext-language_tools.js` | Autovervollständigung | |
| `ext-searchbox.js` | Suchen im Editor | |

- Beim Aktualisieren: neue Dateien nach `vendor/` kopieren, Version und Prüfsummen hier
  aktualisieren und den Lizenztext unten beibehalten.

### Lizenztext

```text
Copyright (c) 2010, Ajax.org B.V.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Ajax.org B.V. nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL AJAX.ORG B.V. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## 2. Sonstiger Fremdcode

**Keiner.** PyPad benutzt ausschließlich die **Python-Standardbibliothek** (json, os, re, signal,
socket, subprocess, sys, tempfile, threading, time, urllib, uuid, webbrowser, http.server,
pathlib, builtins, importlib, keyword, shutil) sowie das Betriebssystem (macOS). Es werden keine
weiteren Bibliotheken, Frameworks, Schriften oder Medien eingebunden. Inhalte der Oberfläche
(HTML, CSS, JavaScript außer Ace) wurden für dieses Projekt selbst geschrieben.

## 3. Prüfsummen der Dateien in `vendor/`

```text
072d13e53d11e2ceccfffe1a0fa7f15cf69c5435d897df53d98c71be1c4a2e7f  vendor/ace.js
799e3a3746f74240d7fbb1a38e525fa01b9718a207f3a50a2550111e11b3a560  vendor/ext-language_tools.js
427ec52caf01e02536f8429adeb2baee82cdd122f2c25cf01663959734019773  vendor/ext-searchbox.js
88eba07c61f5168ebef54323f6e2d31f7e129c05954ea6aa5a3b0a04a2b03aad  vendor/mode-python.js
757fb017f0ff7a6f2b47f30a3ff7bd6211529deceebf07909d4647ae1175a38a  vendor/theme-tomorrow_night.js
```
