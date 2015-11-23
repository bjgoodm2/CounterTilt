/**
 * Created by bgoodman on 11/12/15.
 */

(function () {

    'use strict';

    angular.module('CounterTilt', [])

        .controller('CounterTiltController', ['$scope', '$log', '$http',
            function ($scope, $log, $http) {
                $scope.searchGame = function () {
                    $scope.loading = true;
                    $log.log("test");
                };
            }

        ])
}());