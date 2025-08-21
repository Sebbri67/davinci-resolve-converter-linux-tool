# davinci-resolve-converter-linux-tool
Davinci Resolve (Linux) converter tool

Author : Sebastien Briere

### Note

dvtool_convert.py est un outil de convertion vidéo pour contourner le problème de l'absence de support H264/H265 de la version gratuite de Davinci Resolve.

En effet, la version gratuite de Davinci Resolve ne supporte pas les formats H264/H265, alors que la version professionnelle de Davinci Resolve supporte ces formats.

Les formats supportés nativement par Davinci Resolve sont ProRes 422, DNxHD/HR ou MJPEG.

Il propose les options de conversion suivantes :

## Pour la préparation des imports dans Davinci Resolve
- H264/H265 -> ProRes 422
- H264/H265 -> DNxHD/HR
- H264/H265 -> MJPEG

## Pour les exports de Davinci Resolve
- ProRes 422 -> H264
- ProRes 422  -> H264
- ProRes 422  -> H265

## Les autres options :
- MJPEG -> H264
- MJPEG -> H265
- MJPEG -> H264 (optimisé pour Youtube)
