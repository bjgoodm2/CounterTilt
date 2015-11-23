(function ($) {
    //Function to scroll smoothly down page.  Taken from http://www.learningjquery.com/2007/10/improved-animated-scrolling-script-for-same-page-links
    $(document).ready(function () {
        $('a[href*=#]').click(function () {
            if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '')
                && location.hostname == this.hostname) {
                var $target = $(this.hash);
                $target = $target.length && $target
                    || $('[name=' + this.hash.slice(1) + ']');
                if ($target.length) {
                    var targetOffset = $target.offset().top;
                    $('html,body')
                        .animate({scrollTop: targetOffset}, 1000);
                    return false;
                }
            }
        });
    });

    $(document).ready(function () {
        $('select').material_select();
    });
    $(function () {

        $('.button-collapse').sideNav();
        $('.parallax').parallax();

    });
})(jQuery); // end of jQuery name space