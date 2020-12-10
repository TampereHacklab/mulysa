// submit on language dropdown select
document.getElementById("language-select").addEventListener("change", function() {
    this.form.submit();
});

// higlight required fields in all forms
$('form input[required]').prev('label').addClass('font-weight-bold').after('<span class="text-danger"> *</span>');