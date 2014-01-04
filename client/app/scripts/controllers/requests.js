'use strict';

angular.module('miloprofilerApp')

.controller('RequestsCtrl', ['$scope', '$stateParams', 'Restangular', function($scope, $stateParams, Restangular) {
    Restangular.one('requests', $stateParams.profile).getList().then(function(requests){
        $scope.requests = requests;
        if(requests.length>0){
          var baseDt = Number(requests[0].start);
          angular.forEach($scope.requests, function(request){
                request.offset = Number(request.start) - baseDt;
              });
        }
      });
  }])

.controller('RequestDetailsCtrl', ['$scope', 'Restangular', '$stateParams', '$state', function($scope, Restangular, $stateParams, $state) {
    Restangular.one('requests', $stateParams.profile).one($stateParams.id).get().then(function(rq){
        $scope.request = rq;
      }, function(){
        $state.go('requests', {profile: $stateParams.profile});
      });
  }]);

