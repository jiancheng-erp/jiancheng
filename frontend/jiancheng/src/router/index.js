import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/Pages/LoginPage.vue'
import GeneralManager from '../Pages/GeneralManager/GeneralManager/views/GeneralManager.vue'
import Logistics from '../Pages/LogisticsControlDepartment/LogisticsControlManager/views/LogisticsControlManager.vue'
import ProductionManagementDepartmentGeneral from '../Pages/ProductionManagementDepartment/ProductionManagementDepartmentGeneral/views/ProductionManagementDepartmentGeneral.vue'
import ProductionManager from '../Pages/ProductionManagementDepartment/ProductionManager/views/ProductionManager.vue'
import TechenicalDepartmentClerk from '../Pages/TechnologyDepartment/TechnicalDepartmentClerk/views/TechnicalDepartmentClerk.vue'
import TechnicalManager from '../Pages/TechnologyDepartment/TechnicalManager/views/TechnicalManager.vue'
import HeadOfWareHouse from '../Pages/TotalWarehouse/HeadOfWarehouse/views/HeadOfWarehouse.vue'
import FabricCuttingSupervisor from '../Pages/ProductionManagementDepartment/FabricCuttingSupervisor/views/FabricCuttingSupervisor.vue'
import SewingMachineSupervisor from '../Pages/ProductionManagementDepartment/SewingMachineSupervisor/views/SewingMachineSupervisor.vue'
import MoldingSupervisor from '../Pages/ProductionManagementDepartment/MoldingSupervisor/views/MoldingSupervisor.vue'
import UsageCalculation from '../Pages/UsageCalculation/views/UsageCalculation.vue'
import BusinessManager from '@/Pages/BusinessManager/views/BusinessManager.vue'
import DevelopmentManager from '@/Pages/DevelopmentManager/views/DevelopmentManager.vue'
import HumanResourcesDepartment from '@/Pages/HumanResourcesDepartment/views/HumanResourcesDepartment.vue'
import CompanyManager from '@/Pages/CompanyManger/views/CompanyManager.vue'
import SemifinishedWarehouse from '@/Pages/TotalWarehouse/SemifinishedWarehouse/views/SemifinishedWarehouse.vue'
import FinishedWarehouse from '@/Pages/TotalWarehouse/FinishedWarehouse/views/FinishedWarehouse.vue'
import ProductionClerk from '@/Pages/ProductionManagementDepartment/ProductionClerk/views/ProductionClerk.vue'
import FinancialManager from '@/Pages/FinancialManager/views/FinancialManager.vue'

//引入子路由
import LogisticsRoutes from '../Pages/LogisticsControlDepartment/LogisticsControlManager/routers/logistics'
import ProductionRoutes from '../Pages/ProductionManagementDepartment/ProductionManagementDepartmentGeneral/routers/productionmanagement'
import TechenicalDepartmentClerkRoutes from '../Pages/TechnologyDepartment/TechnicalDepartmentClerk/routers/technicalclerk'
import HeadOfWarehouseRoutes from '../Pages/TotalWarehouse/HeadOfWarehouse/routers/totalWarehouse'
import FabricSupervisorRoutes from '../Pages/ProductionManagementDepartment/FabricCuttingSupervisor/routers/fabricSupervisorRoutes'
import SewingSupervisorRoutes from '../Pages/ProductionManagementDepartment/SewingMachineSupervisor/routers/sewingSupervisorRoutes'
import MoldingSupervisorRoutes from '../Pages/ProductionManagementDepartment/MoldingSupervisor/routers/moldingSupervisorRoutes'
import DeputyGeneral from '@/Pages/ProductionManagementDepartment/ProductionManager/routers/DeputyGeneral'
import UsageCalculationRoutes from '../Pages/UsageCalculation/routers/UsageCalculation'
import DevelopmentManagerRoutes from '@/Pages/DevelopmentManager/routers/DevelopmentManager'
import TechnicalManagerRoutes from '../Pages/TechnologyDepartment/TechnicalManager/routers/technicalManager'
import BusinessManagerRoutes from '../Pages/BusinessManager/routers/business'
import OrderConfirmDetailRoutes from '../Pages/CompanyManger/routers/OrderConfirmDetail'
import ProductionClerkRoutes from '../Pages/ProductionManagementDepartment/ProductionClerk/routers/productionClerk'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    },
    {
      path :'/generalmanager',
      name : 'generalmanager',
      component: GeneralManager,
      meta:{
        requiresAuth: true,
        role: 2
      }
    },
    {
      path :'/logistics',
      name : 'logistics',
      component: Logistics,
      meta:{
        requiresAuth: true,
        role: 9
      }
    },
    {
      path :'/productiongeneral',
      name : 'productiongeneral',
      component: ProductionManagementDepartmentGeneral,
      meta:{
        requiresAuth: true,
        role: 6
      }
    },
    {
      path :'/productionmanager',
      name : 'productionmanager',
      component: ProductionManager,
      meta:{
        requiresAuth: true,
        role: 3
      }
    },
    {
      path :'/technicalclerk',
      name : 'technicalclerk',
      component: TechenicalDepartmentClerk,
      meta:{
        requiresAuth: true,
        role: 17
      }
    },
    {
      path :'/technicalmanager',
      name : 'technicalmanager',
      component: TechnicalManager,
      meta:{
        requiresAuth: true,
        role: 5
      }
    },
    {
      path :'/headofwarehouse',
      name : 'headofwarehouse',
      component: HeadOfWareHouse,
      meta:{
        requiresAuth: true,
        role: 8
      }
    },
    {
      path :'/fabriccutting',
      name : 'fabriccutting',
      component: FabricCuttingSupervisor,
      meta:{
        requiresAuth: true,
        role: 11
      }
    },
    {
      path :'/sewingmachine',
      name : 'sewingmachine',
      component: SewingMachineSupervisor,
      meta:{
        requiresAuth: true,
        role: 12
      }
    },
    {
      path :'/molding',
      name : 'molding',
      component: MoldingSupervisor,
      meta:{
        requiresAuth: true,
        role: 13
      }
    },
    {
      path :'/usagecalculation',
      name : 'usagecalculation',
      component: UsageCalculation,
      meta:{
        requiresAuth: true,
        role: 18
      }
    },
    {
      path :'/businessmanager',
      name : 'businessmanager',
      component: BusinessManager,
      meta:{
        requiresAuth: true,
        role: 4
      }
    },
    {
      path :'/businessmanager',
      name : 'businessmanager',
      component:BusinessManager,
      meta:{
        requirsAuth:true,
        role:21
      }
    },
    {
      path :'/developmentmanager',
      name : 'developmentmanager',
      component: DevelopmentManager,
      meta:{
        requiresAuth: true,
        role: 7
      }
    },
    {
      path :'/humanresourcesdepartment',
      name : 'humanresourcesdepartment',
      component: HumanResourcesDepartment,
      meta:{
        requiresAuth: true,
        role: 14
      }
    },
    {
      path :'/companyManager',
      name : 'companyManager',
      component: CompanyManager,
      meta:{
        requiresAuth: true,
        role: 2
      }
    },
    {
      path :'/semifinishedwarehouse',
      name : 'semifinishedwarehouse',
      component: SemifinishedWarehouse,
      meta:{
        requiresAuth: true,
        role: 19
      }
    },
    {
      path :'/finishedwarehouse',
      name : 'finishedwarehouse',
      component: FinishedWarehouse,
      meta:{
        requiresAuth: true,
        role: 20
      }
    },
    {
      path :'/productionclerk',
      name : 'productionclerk',
      component: ProductionClerk,
      meta:{
        requiresAuth: true,
        role: 22
      }
    },
    {
      path :'/financialManager',
      name : 'financialManager',
      component: FinancialManager,
      meta:{
        requiresAuth: true,
        role: 10
      }
    },
    ...LogisticsRoutes,
    ...ProductionRoutes,
    ...TechenicalDepartmentClerkRoutes,
    ...HeadOfWarehouseRoutes,
    ...FabricSupervisorRoutes,
    ...SewingSupervisorRoutes,
    ...MoldingSupervisorRoutes,
    ...DeputyGeneral,
    ...UsageCalculationRoutes,
    ...DevelopmentManagerRoutes,
    ...TechnicalManagerRoutes,
    ...BusinessManagerRoutes,
    ...OrderConfirmDetailRoutes,
    ...ProductionClerkRoutes
  ]
})
import axios from 'axios'
const apiBaseUrl = router.app?.config?.globalProperties?.$apiBaseUrl

const Logout = () => {
  axios.post(`${apiBaseUrl}/logout`)
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  const userRole = parseInt(localStorage.getItem('role'), 10); // Ensure the role is an integer
  console.log('token', token);
  console.log('userRole', userRole);

  // Check if the route requires authentication
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // If no token, redirect to login
    if (!token) {
      console.log('no token');
      next({ name: 'login' });
    } else {
      const allowedRoles = to.meta.role; // Retrieve the role(s) from meta
      console.log('allowedRoles:', allowedRoles);

      // If the route has a role requirement, check the user's role
      if (allowedRoles) {
        if (Array.isArray(allowedRoles)) {
          // Check if user's role is in the allowed roles array
          if (!allowedRoles.includes(userRole)) {
            Logout();
            next({ name: 'login' });
          } else {
            next();
          }
        } else if (allowedRoles !== userRole) {
          // Handle the case where role is not an array
          Logout();
          next({ name: 'login' });
        } else {
          next();
        }
      } else {
        next();
      }
    }
  } else {
    // If the route doesn't require authentication, proceed as normal
    next();
  }
});

export default router
