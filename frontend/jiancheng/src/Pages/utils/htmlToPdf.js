/**
    path: src/utils/htmlToPdf.js
    name: 导出页面为PDF格式
**/
import html2Canvas from 'html2canvas'
import JsPDF from 'jspdf'

const htmlToPdf = {
    getPdf(title, elementId) {
        const element = document.getElementById(elementId)
        const opts = {
            scale: 4, // 缩放比例，提高生成图片清晰度
            useCORS: true, // 允许加载跨域的图片
            allowTaint: false, // 允许图片跨域，和 useCORS 二者不可共同使用
            tainttest: true, // 检测每张图片都已经加载完成
            logging: true // 日志开关，发布的时候记得改成 false
        }

        html2Canvas(element, opts).then(function (canvas) {
            let contentWidth = canvas.width
            let contentHeight = canvas.height
            let pageHeight = (contentWidth / 592.28) * 841.89
            let leftHeight = contentHeight
            let position = 0
            let imgWidth = 595.28
            let imgHeight = (592.28 / contentWidth) * contentHeight
            let pageData = canvas.toDataURL('image/jpeg', 1.0)
            let PDF = new JsPDF('', 'pt', 'a4')
            if (leftHeight < pageHeight) {
                PDF.addImage(pageData, 'JPEG', 0, 0, imgWidth, imgHeight)
            } else {
                while (leftHeight > 0) {
                    PDF.addImage(pageData, 'JPEG', 0, position, imgWidth, imgHeight)
                    leftHeight -= pageHeight
                    position -= 841.89
                    if (leftHeight > 0) {
                        PDF.addPage()
                    }
                }
            }
            PDF.save(title + '.pdf')
        })
    }
};

export default htmlToPdf;
