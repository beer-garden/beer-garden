import { beforeEach, describe, expect, test, vi, it } from "vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import { CheckUserHasRoles } from "./permission_service";
import { User, Role } from "../models/brewtils-types";
import { PermissionCheck } from "../models/models";
describe("PermissionTesting", () => {

    it.each([
        {access: "READ_ONLY", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "OPERATOR", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "PLUGIN_ADMIN", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "GARDEN_ADMIN", permissionCheck:"GARDEN_ADMIN", expected:true},
        {access: "READ_ONLY", permissionCheck:"PLUGIN_ADMIN", expected:false},
        {access: "OPERATOR", permissionCheck:"PLUGIN_ADMIN", expected:false},
        {access: "PLUGIN_ADMIN", permissionCheck:"PLUGIN_ADMIN", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"PLUGIN_ADMIN", expected:true},
        {access: "READ_ONLY", permissionCheck:"OPERATOR", expected:false},
        {access: "OPERATOR", permissionCheck:"OPERATOR", expected:true},
        {access: "PLUGIN_ADMIN", permissionCheck:"OPERATOR", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"OPERATOR", expected:true},
        {access: "READ_ONLY", permissionCheck:"READ_ONLY", expected:true},
        {access: "OPERATOR", permissionCheck:"READ_ONLY", expected:true},
        {access: "PLUGIN_ADMIN", permissionCheck:"READ_ONLY", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"READ_ONLY", expected:true},
    ])(`Local Access $access Permission $permissionCheck -> $expected`, ({access, permissionCheck, expected})=> {
        const user = {"localRoles":[{"permission":access} as Role]} as User;
        expect(CheckUserHasRoles(user, permissionCheck, {})).toBe(expected);
    });

    it.each([
        {access: "READ_ONLY", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "OPERATOR", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "PLUGIN_ADMIN", permissionCheck:"GARDEN_ADMIN", expected:false},
        {access: "GARDEN_ADMIN", permissionCheck:"GARDEN_ADMIN", expected:true},
        {access: "READ_ONLY", permissionCheck:"PLUGIN_ADMIN", expected:false},
        {access: "OPERATOR", permissionCheck:"PLUGIN_ADMIN", expected:false},
        {access: "PLUGIN_ADMIN", permissionCheck:"PLUGIN_ADMIN", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"PLUGIN_ADMIN", expected:true},
        {access: "READ_ONLY", permissionCheck:"OPERATOR", expected:false},
        {access: "OPERATOR", permissionCheck:"OPERATOR", expected:true},
        {access: "PLUGIN_ADMIN", permissionCheck:"OPERATOR", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"OPERATOR", expected:true},
        {access: "READ_ONLY", permissionCheck:"READ_ONLY", expected:true},
        {access: "OPERATOR", permissionCheck:"READ_ONLY", expected:true},
        {access: "PLUGIN_ADMIN", permissionCheck:"READ_ONLY", expected:true},
        {access: "GARDEN_ADMIN", permissionCheck:"READ_ONLY", expected:true},
    ])(`Upstream Access $access Permission $permissionCheck -> $expected`, ({access, permissionCheck, expected})=> {
        const user = {"upstreamRoles":[{"permission":access} as Role]} as User;
        expect(CheckUserHasRoles(user, permissionCheck, {})).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`Garden Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeGardens": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"gardenName":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`Namespace Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeNamespaces": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"namespace":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`System Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeSystems": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"systemName":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`System Version Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeVersions": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"systemVersion":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`Instance Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeInstances": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"instanceName":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {checkValue: "passed", expected:true},
        {checkValue: "failed", expected:false},
    ])(`System Scope Test Access $checkValue -> $expected`, ({checkValue, expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY", "scopeCommands": [checkValue]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"commandName":"passed"} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {permissionCheck: {"global":true} as PermissionCheck, expected:true},
        {permissionCheck: {"global":true, "gardenName":"failed"} as PermissionCheck, expected:false},
        {permissionCheck: {"global":true, "namespace":"failed"} as PermissionCheck, expected:false},
        {permissionCheck: {"global":true, "systemName":"failed"} as PermissionCheck, expected:false},
        {permissionCheck: {"global":true, "systemVersion":"failed"} as PermissionCheck, expected:false},
        {permissionCheck: {"global":true, "instanceName":"failed"} as PermissionCheck, expected:false},
        {permissionCheck: {"global":true, "commandName":"failed"} as PermissionCheck, expected:false},
    ])(`Global Test Check $permissionCheck -> $expected`, ({permissionCheck , expected})=> {
        const user = {"localRoles":[{"permission":"READ_ONLY"} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", permissionCheck)).toBe(expected);
    });

    it.each([
        {roleCheck: {"permission":"READ_ONLY"} as Role, expected:true},
        {roleCheck: {"permission":"READ_ONLY", scopeGardens:["failed"]} as Role, expected:false},
        {roleCheck: {"permission":"READ_ONLY", scopeNamespaces:["failed"]} as Role, expected:false},
        {roleCheck: {"permission":"READ_ONLY", scopeSystems:["failed"]} as Role, expected:false},
        {roleCheck: {"permission":"READ_ONLY", scopeVersions:["failed"]} as Role, expected:false},
        {roleCheck: {"permission":"READ_ONLY", scopeInstances:["failed"]} as Role, expected:false},
        {roleCheck: {"permission":"READ_ONLY", scopeCommands:["failed"]} as Role, expected:false},
    ])(`Global Test Role $roleCheck -> $expected`, ({roleCheck , expected})=> {
        const user = {"localRoles":[roleCheck]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {"global":true} as PermissionCheck)).toBe(expected);
    });

    it.each([
        {scopeOne:"scopeGardens", scopeTwo:"scopeNamespaces", expected:true},
    ])(`Wildcard Role $scopeOne & $scopeTwo -> $expected`, ({scopeOne, scopeTwo , expected})=> {
        const user = {"localRoles":[{[scopeOne]: ["passed"], [scopeTwo]: ["passed"]} as Role]} as User;
        expect(CheckUserHasRoles(user, "READ_ONLY", {gardenName:"passed", namespace:"passed", systemName:"passed", systemVersion:"passed", instanceName:"passed", commandName:"passed"} as PermissionCheck)).toBe(expected);
    });



});