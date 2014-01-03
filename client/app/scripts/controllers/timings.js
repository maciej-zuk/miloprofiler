'use strict';

angular.module('miloprofilerApp')

.controller('TimingsCtrl', ['$scope', 'Restangular', function($scope, Restangular) {
    Restangular.all('timings').getList().then(function(timings){
        $scope.timings = timings;
    });
}])

.controller('TimingDetailsCtrl', ['$scope', 'Restangular', '$stateParams', '$state', function($scope, Restangular, $stateParams, $state) {
    Restangular.one('timings', $stateParams.id).get().then(function(timing){
        $scope.timing = timing;
    }, function(){
        $state.transitionTo('timings');
    });
}]);

