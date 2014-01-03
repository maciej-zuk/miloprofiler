'use strict';

angular.module('miloprofilerApp')

.controller('RequestsCtrl', ['$scope', 'Restangular', function($scope, Restangular) {
    Restangular.all('requests').getList().then(function(requests){
        $scope.requests = requests;
        if(requests.length>0){
            var base_dt = Number(requests[0].start);
            angular.forEach($scope.requests, function(request){
                request.offset = Number(request.start) - base_dt;
            });
        }
    });
}])

.controller('RequestDetailsCtrl', ['$scope', 'Restangular', '$stateParams', '$state', function($scope, Restangular, $stateParams, $state) {
    Restangular.one('requests', $stateParams.id).get().then(function(rq){
        $scope.request = rq;
    }, function(){
        $state.transitionTo('requests');
    });
}]);

