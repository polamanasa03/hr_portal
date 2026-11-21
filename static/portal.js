const profileTrigger=document.getElementById('profileTrigger');
const profileMenu=document.getElementById('profileMenu');
profileTrigger?.addEventListener('click',()=>profileMenu.classList.toggle('show'));
document.addEventListener('click',event=>{if(profileMenu&&!profileMenu.contains(event.target)&&!profileTrigger.contains(event.target))profileMenu.classList.remove('show')});
const preview=document.getElementById('preview');
const closePreview=()=>{preview.hidden=true;document.body.style.overflow=''};
document.querySelectorAll('.doc-open').forEach(button=>button.addEventListener('click',()=>{
 const doc=window.PORTAL_DOCS.find(item=>item.id===button.dataset.doc); if(!doc)return;
 document.getElementById('previewName').textContent=doc.name;document.getElementById('paperName').textContent=doc.name;
 document.getElementById('paperDescription').textContent=doc.description+' The information contained in this document has been verified by the People Operations team and is available for official use.';
 document.getElementById('paperDate').textContent=doc.date;document.getElementById('detailCategory').textContent=doc.category;
 document.getElementById('detailSize').textContent=doc.size;document.getElementById('detailDate').textContent=doc.date;
 document.getElementById('detailId').textContent=doc.doc_id;document.getElementById('previewDownload').href=`/documents/${doc.id}/download`;
 document.querySelector('.pill').textContent=doc.category.toUpperCase();preview.hidden=false;document.body.style.overflow='hidden';
}));
document.getElementById('closePreview')?.addEventListener('click',closePreview);
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',closePreview));
preview?.addEventListener('click',event=>{if(event.target===preview)closePreview()});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&preview&&!preview.hidden)closePreview()});
